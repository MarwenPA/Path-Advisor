# Login & Password Reset — DPO Runbook

**Owners:** DPO / Engineering on-call
**Story:** 1.5 (login + per-account lockout + password reset).

This runbook covers the login security model and the DPO playbooks for the
two most common support escalations: "I'm locked out" and "I want to reset
a user's password without their email working".

---

## 1. Defense-in-depth layers

Two rate-limit shapes protect the login endpoint:

| Layer | Scope | Trigger | Where |
|---|---|---|---|
| **Per-IP throttle** | 5/min/IP | django-ratelimit on `ThrottledLoginView.dispatch` | Story 1.12 |
| **Per-account lockout** | 5 fails / 15 min → 10 min lock | `login_security.record_failed_attempt` | Story 1.5 |

They are **orthogonal**:
- A single botnet IP hammering many emails trips the per-IP throttle without filling any per-account counter.
- A distributed attack on one email (multiple IPs) trips the per-account lockout without exhausting any single IP's budget.

The lockout state lives on `User.locked_until` (DB column, source of truth). The Redis counter (`auth.login_fail:{user_id}` with TTL 900s) feeds the threshold check but is allowed to lose data on a cache flush — the lockout itself never lapses early.

---

## 2. Audit-log events

See [docs/patterns/audit-events.md §Story 1.5](../patterns/audit-events.md) for the canonical catalog. Quick reference:

| Action | When |
|---|---|
| `auth.login_succeeded` | 200 from login endpoint |
| `auth.login_failed` | Wrong password / unknown email / suspended / unverified / deleted |
| `auth.login_blocked_locked` | Login attempt while `locked_until > now()` |
| `auth.account_locked` | Threshold trip (N-th failure within window) |
| `auth.password_reset_requested` | KNOWN email hit the request endpoint |
| `auth.password_reset_requested_unknown` | UNKNOWN email hit the request endpoint (DPO enumeration signal) |
| `auth.password_reset_completed` | Confirm endpoint 200 (sessions purged, lockout cleared) |

**DPO enumeration query** — same `ip_truncated` against many `subject_id`s or many `auth.password_reset_requested_unknown` from one IP = active probing.

---

## 3. "I'm locked out" — user support flow

Triage step 1: ask the user when they last successfully logged in. If the last `auth.login_succeeded` is recent (< 1 day), they probably forgot the new password — route them through the **password reset flow** (next section), which automatically clears the lockout column on confirm.

If they insist they typed the right password OR the lockout fired immediately after they verified the new account email, check the audit log:

```python
# manage.py shell
from apps.audit.models import AuditLog
AuditLog.objects.filter(
    subject_id="<user_id>",
).order_by("-created_at")[:20]
```

A burst of `auth.login_failed` rows from the SAME `ip_truncated` confirms the lockout was a defensive trigger — the user can wait 10 minutes (default `LOGIN_LOCK_DURATION_SECONDS`).

**Manual unlock (emergency, e.g. C-level user, demo before customer):**

```python
# manage.py shell
from apps.accounts.models import User
from apps.accounts.services import login_security
user = User.objects.get(email="alice@example.test")
login_security.clear_failed_attempts(user=user)
user.refresh_from_db()
assert user.locked_until is None
```

This clears both the Redis counter AND the `locked_until` column. Audit row `auth.account_locked` from the trip remains for compliance (it's append-only).

---

## 4. "I can't access my email — please reset my password" — DPO override

The self-service password-reset flow assumes the user has email access. When they don't (lost the inbox, mistyped during signup), the DPO follows this manual procedure after verifying identity out-of-band (callback, document, etc.):

```python
# manage.py shell
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from apps.accounts.models import User

user = User.objects.get(email="alice@example.test")
uid = urlsafe_base64_encode(force_bytes(user.pk))
token = default_token_generator.make_token(user)
print(f"https://path-advisor.fr/auth/reset-password/{uid}/{token}")
```

Send the link out-of-band (Slack DM, signed email from `dpo@path-advisor.fr`, in-person on a smartphone, …). The link is valid 1 hour (`PASSWORD_RESET_TIMEOUT = 3600`). The user lands on the SPA confirm page, picks a password, lands on `/auth/login?reset=success`.

**Why not `user.set_password(new_pwd)` directly?** That skips the `auth.password_reset_completed` audit row, the session purge, the lockout clearance, and the confirmation email. The reset flow is the safer path.

Alternative: if no email + no out-of-band channel works (true edge case), drop into shell and call the side-effect helpers individually:

```python
from apps.accounts.services import login_security
from apps.accounts.services.session_utils import terminate_user_sessions
from apps.audit.decorators import record_audit
from apps.audit.models import AuditResult

user.set_password("TempPwd-2026-must-rotate!")
user.save(update_fields=["password"])
login_security.clear_failed_attempts(user=user)
terminate_user_sessions(user)
record_audit(
    action="auth.password_reset_completed",
    result=AuditResult.SUCCESS,
    actor=dpo_user,  # YOUR user, not the target
    subject_id=user.id,
    metadata={"via": "dpo_shell_override", "reason": "out-of-band recovery"},
)
```

Then communicate the temporary password out-of-band and instruct the user to log in + change it via the reset flow ASAP.

---

## 5. Open items (deferred)

- **Timing-side-channel on the reset endpoint** — the existence check + SMTP queue produce a slightly slower path for known emails. Per-IP 5/h cap is the MVP mitigation; revisit when abuse surfaces.
- **`gdpr_exceptions.py` rename** — the file is now broader than its name (covers all auth Problem Details since Story 1.12 + 1.5). Cleanup in a Sprint-3 refactor story.
- **MFA hook in `PathAdvisorLoginSerializer`** — Story 1.6 will intercept the success path to inject `{"mfa_required": true, "mfa_session": "..."}` for staff users instead of setting the session cookie.
