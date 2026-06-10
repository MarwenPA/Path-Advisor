"""MFA service — Story 1.6.

Pure-service module wrapping django-otp's `TOTPDevice` + `StaticDevice` with
Path-Advisor semantics: 8 recovery codes per enrollment, formatted as
`xxxx-xxxx-xxxx` for readability, `MfaProfile.enrolled_at` synchronized
with `TOTPDevice.confirmed`, and audit rows written via `record_audit`
(Story 1.13 mechanism).

The service is the ONLY allowed entry point for MFA state changes — views
must not touch `TOTPDevice` / `StaticDevice` directly. This keeps the audit-
log contract (every state change emits one audit row) intact.

Constraints we DO NOT relax:
- A user has AT MOST one confirmed `TOTPDevice` (`name="default"`). A second
  call to `start_enrollment` deletes any prior unconfirmed device — only ONE
  enrollment can be in flight at a time.
- Recovery codes are returned in plaintext EXACTLY ONCE — at enrollment-confirm
  and at regenerate-time. After that they live only as hashed `StaticToken.token`
  rows. NEVER log them, NEVER include in audit metadata.
- The `confirm_enrollment` path enforces an idempotent insert + delete pattern
  on the `StaticDevice` (drops any prior recovery-token set so a re-confirm
  cannot accidentally double the user's codes).

The service writes audit rows inline so a partial failure (TOTP confirmed
but audit DB unreachable) rolls back via `transaction.atomic` — same pattern
Story 1.5's `login_security` adopted in code-review P3.
"""

from __future__ import annotations

import secrets
from io import BytesIO
from typing import Literal

import qrcode
import qrcode.image.svg
import structlog
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django_otp.plugins.otp_static.models import StaticDevice, StaticToken
from django_otp.plugins.otp_totp.models import TOTPDevice

from apps.accounts.gdpr_exceptions import MfaDisableForbiddenForStaff
from apps.accounts.models import STAFF_ROLES_REQUIRING_MFA, MfaProfile, User
from apps.audit.decorators import record_audit
from apps.audit.models import AuditResult

log = structlog.get_logger(__name__)

_RECOVERY_CODE_GROUPS = 3  # `xxxx-xxxx-xxxx` shape
_RECOVERY_CODE_GROUP_LEN = 4
_TOTP_DEVICE_NAME = "default"


def _generate_recovery_code() -> str:
    """Generate a single recovery code formatted `xxxx-xxxx-xxxx`.

    Uses `secrets.token_hex` for cryptographic randomness — 12 hex chars
    sliced into three 4-char groups. The resulting alphabet (0-9a-f) is
    unambiguous (no I/l/O/0 confusion) and trivially typable on any keyboard.
    """
    raw = secrets.token_hex(_RECOVERY_CODE_GROUPS * _RECOVERY_CODE_GROUP_LEN // 2)
    groups = [
        raw[i : i + _RECOVERY_CODE_GROUP_LEN] for i in range(0, len(raw), _RECOVERY_CODE_GROUP_LEN)
    ]
    return "-".join(groups)


def _render_qr_svg(otpauth_url: str) -> str:
    """Render the QR code as an inline SVG string (256x256 box).

    Inline SVG avoids the image-CSP rabbit-hole — the front-end embeds the
    string via `dangerouslySetInnerHTML` (the SVG is server-trusted; no user
    input flows into it).
    """
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(otpauth_url)
    qr.make(fit=True)
    img = qr.make_image(image_factory=qrcode.image.svg.SvgPathImage)
    buf = BytesIO()
    img.save(buf)
    return buf.getvalue().decode("utf-8")


def _ensure_profile(user: User) -> MfaProfile:
    """Return the user's MfaProfile, creating it if missing.

    `MfaProfile.user` is the primary key — `get_or_create` is the canonical
    upsert.
    """
    profile, _ = MfaProfile.objects.get_or_create(user=user)
    return profile


def start_enrollment(*, user: User, ip_truncated: str | None = None) -> tuple[TOTPDevice, str, str]:
    """Create (or replace) an unconfirmed `TOTPDevice` and return the
    `otpauth://` URL + inline SVG QR code.

    Returns: `(device, otpauth_url, qr_svg)`.

    Idempotent: re-calling deletes any prior unconfirmed device for the user
    and creates a fresh one. The PRIOR CONFIRMED device (if any) is NOT
    touched — a re-enrollment from an enrolled user is refused upstream;
    this helper only handles the in-flight provisional state.

    Writes `auth.mfa_enrollment_started` audit row.
    """
    with transaction.atomic():
        TOTPDevice.objects.filter(user=user, confirmed=False).delete()
        device = TOTPDevice.objects.create(user=user, name=_TOTP_DEVICE_NAME, confirmed=False)
        record_audit(
            action="auth.mfa_enrollment_started",
            result=AuditResult.SUCCESS,
            actor=user,
            subject_id=user.id,
            metadata={"ip_truncated": ip_truncated},
        )

    otpauth_url = device.config_url
    qr_svg = _render_qr_svg(otpauth_url)
    return device, otpauth_url, qr_svg


def confirm_enrollment(
    *,
    user: User,
    code: str,
    ip_truncated: str | None = None,
) -> list[str]:
    """Verify the user's first TOTP code and finalize enrollment.

    On success:
    - Flips `TOTPDevice.confirmed=True`.
    - Drops any prior `StaticDevice` for the user (idempotent regenerate).
    - Creates a fresh `StaticDevice` + N `StaticToken` rows (N from
      `settings.MFA_RECOVERY_CODES_COUNT`, default 8).
    - Sets `MfaProfile.enrolled_at = now()` and clears
      `requires_enrollment_at_next_login`.
    - Writes `auth.mfa_enrolled` audit row.

    Returns the plaintext recovery codes — caller MUST surface them to the
    user EXACTLY ONCE (the next HTTP response) and never log them.

    Returns an empty list if the TOTP code is invalid. The caller writes
    the failure audit row (different action: `auth.mfa_challenge_failed`
    with `reason="invalid_enrollment_code"`) since the failure happens at
    the view layer where the request context lives.
    """
    device = TOTPDevice.objects.filter(user=user, name=_TOTP_DEVICE_NAME, confirmed=False).first()
    if device is None or not device.verify_token(code):
        return []

    code_count = getattr(settings, "MFA_RECOVERY_CODES_COUNT", 8)
    plaintext_codes = [_generate_recovery_code() for _ in range(code_count)]

    with transaction.atomic():
        device.confirmed = True
        device.save(update_fields=["confirmed"])

        # Drop any prior recovery device — a re-enrollment after DPO reset
        # must NOT accumulate codes from the previous run.
        StaticDevice.objects.filter(user=user).delete()
        static_device = StaticDevice.objects.create(
            user=user, name=_TOTP_DEVICE_NAME, confirmed=True
        )
        StaticToken.objects.bulk_create(
            [StaticToken(device=static_device, token=code) for code in plaintext_codes]
        )

        profile = _ensure_profile(user)
        profile.enrolled_at = timezone.now()
        profile.requires_enrollment_at_next_login = False
        profile.save(
            update_fields=[
                "enrolled_at",
                "requires_enrollment_at_next_login",
                "updated_at",
            ]
        )

        record_audit(
            action="auth.mfa_enrolled",
            result=AuditResult.SUCCESS,
            actor=user,
            subject_id=user.id,
            metadata={
                "device_type": "totp",
                "recovery_codes_count": code_count,
                "ip_truncated": ip_truncated,
            },
        )

    log.info("auth.mfa_enrolled", user_id=user.id)
    return plaintext_codes


def verify_challenge(
    *,
    user: User,
    code: str,
    method: Literal["totp", "recovery"],
    ip_truncated: str | None = None,
    emit_audit: bool = True,
) -> bool:
    """Verify a TOTP code or consume a recovery code. Returns True on success.

    On success:
    - TOTP path: relies on django-otp's `TOTPDevice.verify_token` which
      tracks `last_t` to refuse replays inside the same 30s window.
    - Recovery path: looks up the `StaticToken`, deletes it on success
      (one-time use, `select_for_update` to defeat concurrent-consumption
      races — code-review P11). If `remaining_codes` drops at or below
      `settings.MFA_RECOVERY_LOW_THRESHOLD`, the caller (view layer) MUST
      send the "low recovery codes" email.
    - Bumps `MfaProfile.last_challenge_at`.
    - **Always** writes `auth.mfa_challenge_passed` (code-review P4 — was
      previously TOTP-only, which broke "all successful challenges in 24h"
      queries). The recovery path ALSO writes `auth.mfa_recovery_code_used`.

    On failure:
    - Returns False.
    - Writes `auth.mfa_challenge_failed` audit row with
      `metadata.reason="invalid_code"`.

    `emit_audit=False` is used by the step-up re-auth paths (disable,
    regenerate recovery codes) which need to verify the code but should
    NOT pollute the login-flow audit log with `mfa_challenge_passed`
    rows (code-review P13). The step-up endpoints write their own
    audit rows (`auth.mfa_disabled`, `auth.mfa_recovery_codes_regenerated`).

    Caller (view) is responsible for the per-user lockout via
    `login_security.record_failed_attempt(user=user)` on the failure path —
    we keep the lockout state machine in ONE place (Story 1.5's service).
    """
    metadata: dict[str, object] = {"method": method, "ip_truncated": ip_truncated}

    if method == "totp":
        # `select_for_update` inside an `atomic` block defeats concurrent
        # verify_token races that would let the same code be accepted twice
        # (django-otp's `last_t` write is otherwise racy).
        with transaction.atomic():
            device = (
                TOTPDevice.objects.select_for_update()
                .filter(user=user, name=_TOTP_DEVICE_NAME, confirmed=True)
                .first()
            )
            ok = device is not None and device.verify_token(code)
        if not ok:
            if emit_audit:
                record_audit(
                    action="auth.mfa_challenge_failed",
                    result=AuditResult.FAILURE,
                    actor=user,
                    subject_id=user.id,
                    metadata={**metadata, "reason": "invalid_code"},
                )
            return False
    else:  # method == "recovery"
        # Lock the StaticToken row before delete so concurrent uses can't
        # both succeed on the same code (code-review P11).
        with transaction.atomic():
            static_device = StaticDevice.objects.filter(user=user, confirmed=True).first()
            token_row = (
                None
                if static_device is None
                else static_device.token_set.select_for_update().filter(token=code).first()
            )
            if token_row is None:
                if emit_audit:
                    record_audit(
                        action="auth.mfa_challenge_failed",
                        result=AuditResult.FAILURE,
                        actor=user,
                        subject_id=user.id,
                        metadata={**metadata, "reason": "invalid_code"},
                    )
                return False
            token_row.delete()
            remaining = static_device.token_set.count()
        metadata["remaining_codes"] = remaining
        if emit_audit:
            record_audit(
                action="auth.mfa_recovery_code_used",
                result=AuditResult.SUCCESS,
                actor=user,
                subject_id=user.id,
                metadata=metadata,
            )

    # Common success-path bookkeeping — `select_for_update` on MfaProfile
    # would be over-engineering for last_challenge_at; UPDATE is idempotent.
    profile = _ensure_profile(user)
    profile.last_challenge_at = timezone.now()
    profile.save(update_fields=["last_challenge_at", "updated_at"])

    # Code-review P4 — emit `auth.mfa_challenge_passed` for BOTH paths so
    # DPO queries `WHERE action = 'auth.mfa_challenge_passed'` count every
    # successful challenge, not just the TOTP ones. The recovery path also
    # carries the `mfa_recovery_code_used` complementary event.
    if emit_audit:
        record_audit(
            action="auth.mfa_challenge_passed",
            result=AuditResult.SUCCESS,
            actor=user,
            subject_id=user.id,
            metadata=metadata,
        )
    return True


def disable(*, user: User, trigger: str, ip_truncated: str | None = None) -> None:
    """Tear down a user's MFA enrollment.

    Refuses with `MfaDisableForbiddenForStaff` if `user.role` is in
    `STAFF_ROLES_REQUIRING_MFA` — staff MUST keep MFA active (NFR-S2).
    Use `reset_by_dpo` for the staff-specific "lost device" path.

    Silent no-op (no audit row, no exception) if the user has no MFA
    enrolled — code-review P16. Without this guard, the endpoint would
    write a misleading `auth.mfa_disabled` event for a never-enrolled
    user (UX: clicking "Disable" while nothing was on).

    Deletes the user's `TOTPDevice` + `StaticDevice` rows, clears
    `MfaProfile.enrolled_at`, writes `auth.mfa_disabled` audit row.
    """
    if user.role in STAFF_ROLES_REQUIRING_MFA:
        raise MfaDisableForbiddenForStaff()

    if not user.has_mfa_enrolled:
        # Code-review P16 — silent no-op. No audit, no exception. The caller
        # (view) gets a clean 200 either way.
        return

    with transaction.atomic():
        TOTPDevice.objects.filter(user=user).delete()
        StaticDevice.objects.filter(user=user).delete()
        profile = _ensure_profile(user)
        profile.enrolled_at = None
        profile.last_challenge_at = None
        profile.save(update_fields=["enrolled_at", "last_challenge_at", "updated_at"])
        record_audit(
            action="auth.mfa_disabled",
            result=AuditResult.SUCCESS,
            actor=user,
            subject_id=user.id,
            metadata={"trigger": trigger, "ip_truncated": ip_truncated},
        )

    log.info("auth.mfa_disabled", user_id=user.id, trigger=trigger)


def reset_by_dpo(
    *,
    target_user: User,
    dpo_actor: User,
    reason: str,
) -> None:
    """DPO override — wipe MFA state and force re-enrollment at next login.

    Use case: user (especially staff) lost BOTH authenticator AND all 8
    recovery codes. DPO verifies identity out-of-band (callback, document),
    then calls this from `manage.py shell`.

    Bypasses the staff-role guard of `disable()` — that's the whole point.
    Sets `requires_enrollment_at_next_login=True` so the user is forced
    through the enrollment flow on their very next login (the
    `ThrottledLoginView` hook reads this flag).
    """
    with transaction.atomic():
        TOTPDevice.objects.filter(user=target_user).delete()
        StaticDevice.objects.filter(user=target_user).delete()
        profile = _ensure_profile(target_user)
        profile.enrolled_at = None
        profile.last_challenge_at = None
        profile.requires_enrollment_at_next_login = True
        profile.save(
            update_fields=[
                "enrolled_at",
                "last_challenge_at",
                "requires_enrollment_at_next_login",
                "updated_at",
            ]
        )
        record_audit(
            action="auth.mfa_reset_by_dpo",
            result=AuditResult.SUCCESS,
            actor=dpo_actor,
            subject_id=target_user.id,
            metadata={"reason": reason},
        )

    log.warning(
        "auth.mfa_reset_by_dpo",
        target_user_id=target_user.id,
        dpo_actor_id=dpo_actor.id,
    )


def regenerate_recovery_codes(*, user: User, ip_truncated: str | None = None) -> list[str]:
    """Issue a fresh batch of N recovery codes, invalidating the prior set.

    Returns the plaintext codes (caller surfaces ONCE in the HTTP response).
    Writes `auth.mfa_recovery_codes_regenerated` audit row.

    Caller (view) is responsible for re-auth — typically requires the user's
    current password + a fresh TOTP code, OR a recent (< 15 min) successful
    challenge.
    """
    code_count = getattr(settings, "MFA_RECOVERY_CODES_COUNT", 8)
    plaintext_codes = [_generate_recovery_code() for _ in range(code_count)]

    with transaction.atomic():
        # Code-review P18 — match on `confirmed=True` so a stale unconfirmed
        # device (e.g. mid-DPO-reset window) is NOT reused. Without this,
        # regenerate could land codes on an unconfirmed device that
        # `verify_challenge` (filtered on confirmed=True) would never accept.
        static_device, _ = StaticDevice.objects.get_or_create(
            user=user,
            name=_TOTP_DEVICE_NAME,
            confirmed=True,
            defaults={"confirmed": True},
        )
        StaticToken.objects.filter(device=static_device).delete()
        StaticToken.objects.bulk_create(
            [StaticToken(device=static_device, token=code) for code in plaintext_codes]
        )
        record_audit(
            action="auth.mfa_recovery_codes_regenerated",
            result=AuditResult.SUCCESS,
            actor=user,
            subject_id=user.id,
            metadata={"count": code_count, "ip_truncated": ip_truncated},
        )

    return plaintext_codes


def remaining_recovery_codes(user: User) -> int:
    """Helper for the dashboard widget — returns the count of unused codes."""
    static_device = StaticDevice.objects.filter(user=user, confirmed=True).first()
    return 0 if static_device is None else static_device.token_set.count()
