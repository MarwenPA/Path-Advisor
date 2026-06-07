# MFA lost device — DPO Runbook

**Owners:** DPO / Security on-call
**Story:** 1.6 (MFA TOTP enrollment + challenge + recovery).
**Related:** [`docs/runbooks/login-and-password-reset.md`](./login-and-password-reset.md) for password-reset / lockout DPO playbooks.

This runbook covers the "I lost my authenticator AND my 8 recovery codes" support escalation. By design this is the ONLY path back into an enrolled staff account (counselor / school_admin / path_admin) — the self-service `mfa/disable/` endpoint is hard-refused for staff (NFR-S2). B2C users (student / parent) can self-disable, but the DPO override is still the fallback when both their authenticator AND recovery codes are gone.

---

## 1. Threat model — why this is a careful flow

The DPO override completely unlocks the user's account: their existing TOTP device + 8 recovery codes are wiped, and the next login forces re-enrollment with a fresh QR code. An attacker who can social-engineer the DPO into running `reset_by_dpo` against another user's account gets a clean MFA-free login at the next attempt (just needs the password — which they may have phished separately).

So this is NOT a "any support agent can do it" path. The procedure:
1. **Identity verification** — out-of-band callback to a phone number on file, OR signed PDF document, OR in-person at an office. NEVER rely solely on the email account being compromised.
2. **Audit trail** — every `reset_by_dpo` call writes `auth.mfa_reset_by_dpo` with `actor=<dpo_user>`, `subject=<target_user>`, `metadata.reason=<free text>`. Reviews can replay every DPO decision later.
3. **DPO sign-off** — if the user is `path_admin` (system root), require a second DPO to validate. This is operational discipline (no enforcement in code yet — added when admin UI lands).

---

## 2. The shell procedure

After identity verification, run from inside the Django shell on a production-bastion host:

```python
# manage.py shell
from apps.accounts.models import User
from apps.accounts.services.mfa import reset_by_dpo

target = User.objects.get(email="conseillere.qui-a-perdu@example.test")
dpo = User.objects.get(email="dpo@path-advisor.fr")  # YOUR account

reset_by_dpo(
    target_user=target,
    dpo_actor=dpo,
    reason="Vol du smartphone + perte des codes de récupération - vérification téléphone OOB 2026-06-03",
)
```

This:
- Deletes the user's `TOTPDevice` + `StaticDevice` rows (any prior recovery codes are immediately invalidated even if the attacker had them stashed).
- Sets `MfaProfile.requires_enrollment_at_next_login = True` so the user is forced through the enrollment flow on their very next login.
- Writes the `auth.mfa_reset_by_dpo` audit row.

**Verify:**

```python
target.refresh_from_db()
assert target.has_mfa_enrolled is False
assert target.mfa_profile.requires_enrollment_at_next_login is True
```

---

## 3. Communicate the next step to the user

Out-of-band (call back, signed email from `dpo@path-advisor.fr`):

> Bonjour,
>
> Comme convenu, j'ai réinitialisé ta MFA. À ta prochaine connexion sur Path-Advisor :
>
> 1. Connecte-toi avec ton email + mot de passe habituels.
> 2. Tu seras redirigé vers l'écran d'enrôlement MFA.
> 3. Scanne le nouveau QR code avec ton application authenticator (Google Authenticator, Authy, 1Password, etc.).
> 4. **Note immédiatement les 8 codes de récupération** dans un endroit sûr (gestionnaire de mots de passe, papier dans un coffre, etc.). Ils sont uniques et tu ne les reverras jamais.
>
> Si quelque chose ne va pas, réponds à ce mail.
>
> [DPO Name], DPO Path-Advisor

---

## 4. Emergency operations — disable MFA for a B2C user via DPO

Same flow as staff above; the `reset_by_dpo` helper works for ALL roles. Use it whenever the user can't reach their authenticator AND their recovery codes (regardless of role). The post-reset behaviour is identical: next login forces re-enrollment.

**Alternative for B2C only** — if the user just wants MFA gone (not re-enrolled), they can use the self-service `POST /api/v1/auth/mfa/disable/` endpoint AFTER they regain access. The DPO override is the only path when both factors are lost.

---

## 5. Audit-log queries (DPO triage)

Common questions:

**"How many DPO resets happened in the last 30 days?"**

```python
from apps.audit.models import AuditLog
from django.utils import timezone
from datetime import timedelta

AuditLog.objects.filter(
    action="auth.mfa_reset_by_dpo",
    created_at__gte=timezone.now() - timedelta(days=30),
).count()
```

**"Who reset whose MFA last week?"**

```python
AuditLog.objects.filter(
    action="auth.mfa_reset_by_dpo",
    created_at__gte=timezone.now() - timedelta(days=7),
).values("actor_id", "subject_id", "metadata", "created_at")
```

**"Is there a pattern of failed enrollments after a reset (re-enrollment going wrong)?"**

```python
# Pair each reset with the user's subsequent mfa_enrollment_started / _enrolled
reset = AuditLog.objects.filter(action="auth.mfa_reset_by_dpo")
for r in reset:
    subsequent = AuditLog.objects.filter(
        subject_id=r.subject_id,
        action__startswith="auth.mfa_",
        created_at__gt=r.created_at,
    ).order_by("created_at")[:5]
    print(r.subject_id, r.created_at, [s.action for s in subsequent])
```

---

## 6. Why no admin UI yet?

The `manage.py shell` path is deliberately friction-full. Until the MVP volume justifies a polished admin action (Sprint 4+), the shell + runbook combo:
- Forces the DPO to think before running.
- Makes the audit row explicit (`actor`, `reason` both mandatory).
- Avoids the "any admin can click a button" attack surface.

When the admin UI lands, it MUST replicate the same audit-row write and require the DPO to type the `reason` in a free-text field that's persisted to the metadata.

---

## 7. Open items (deferred)

- **`requires_enrollment_at_next_login` no decay** — a staff user reset but who never logs back in keeps the flag forever. Tracked as deferred-work (Story 1.6 §6 #1).
- **WebAuthn for `path_admin`** — TOTP is the MVP. WebAuthn for the most-privileged role flagged in `core-architectural-decisions.md` §44 as growth.
- **Audit row email to user on `reset_by_dpo`** — currently the DPO communicates via out-of-band channel; an automated "Your MFA was reset by support" email would be a nice belt-and-braces signal. Add when email transactional infra lands (Story 8.1).
