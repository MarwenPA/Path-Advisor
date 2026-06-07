"""MFA session token — Story 1.6 §AC10 + code-review patches 2026-06-04.

Short-lived (5-min default), IP-bound (/24 IPv4, /48 IPv6 bucket), single-use
token issued at password-success when the user has `requires_mfa=True`.

Carries the user id and a `stage` (`mfa_pending` for challenge,
`mfa_enrollment_pending` for first-time enrollment). The MFA challenge /
enrollment-confirm endpoints consume it to authenticate the user WITHOUT
a session cookie — because the session cookie is ONLY posted after the
full login (password + MFA) completes.

**Design choices (post code-review 2026-06-04):**

- Signed via Django's `TimestampSigner` (HMAC + SECRET_KEY) — no JWT library
  added; stdlib + Django pieces are sufficient.
- 5-min TTL — long enough to scan a QR + type the code, short enough to
  invalidate fast on shoulder-surfing of the URL hash.
- **IP-binding coarsened to /24 (IPv4) / /48 (IPv6)** (code-review D1) —
  strict per-IP binding caused false positives for users on carrier-grade
  NAT, mobile networks switching cell towers, corporate proxies with
  multi-egress. The /24 bucket still catches cross-org replays without
  punishing legitimate roaming.
- **Single-use blacklist + per-token fail counter** (code-review P28) —
  successful `consume()` blacklists the JTI; the failure counter
  (`mfa_session_fails:<jti>`) blacklists after 3 consecutive bad codes,
  closing the brute-force-within-token window. Both keys self-expire on
  the TTL.
- **Best-effort Redis writes** (code-review P8) — `consume()` and the
  fail-counter writes catch `Exception` and log; a Redis outage degrades
  to "less anti-replay" rather than breaking the login flow.
- **Strict TTL on `consume()`** (code-review P10) — was lenient
  `max_age=ttl*2`; tightened to `max_age=ttl`. An expired token cannot be
  blacklisted post-hoc.
- **Distinct `MfaSessionConsumed` exception** (code-review P15) — split
  from the generic `MfaSessionInvalid` so the frontend can distinguish
  "already used" (refresh / replay) from "tampered / signature failure".
  IP mismatch + wrong stage remain `MfaSessionInvalid` (anti-enum: don't
  tell attackers which side mismatched).
- **Payload-type validation** (code-review P9) — `json.loads` could
  return a non-dict; defensive `isinstance(payload, dict)` check.
"""

from __future__ import annotations

import hashlib
import ipaddress
import json
import secrets
from typing import Literal

import structlog
from django.conf import settings
from django.core.cache import cache
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner

from apps.accounts.gdpr_exceptions import (
    MfaSessionConsumed,
    MfaSessionExpired,
    MfaSessionInvalid,
)
from apps.accounts.models import User

log = structlog.get_logger(__name__)

Stage = Literal["mfa_pending", "mfa_enrollment_pending"]

_SIGNER_SALT = "mfa-session-token"
_BLACKLIST_KEY_PREFIX = "mfa_session_blacklist:"
_FAIL_COUNTER_KEY_PREFIX = "mfa_session_fails:"
_USE_COUNTER_KEY_PREFIX = "mfa_session_uses:"

#: Number of consecutive failed challenge attempts allowed against a single
#: `mfa_session` token before the JTI is blacklisted server-side (code-review
#: P28 — closes the brute-force-within-token window).
MAX_FAILS_PER_TOKEN = 3

#: Number of `enroll/start/` calls allowed against a single `mfa_session`
#: token (the user may need 2-3 retries if they fat-finger the QR scan)
#: before the JTI is blacklisted (code-review P1 — caps replay).
MAX_USES_PER_TOKEN = 3


def _coarsen_ip(ip: str | None) -> str:
    """Bucket the IP into /24 IPv4 or /48 IPv6 before hashing.

    Avoids spurious `MfaSessionInvalid` for users on rotating egress IPs
    (carrier NAT, mobile, corporate proxy) while still binding the token
    to a small enough subnet to defeat cross-org replay.
    """
    if not ip:
        return "unknown"
    try:
        addr = ipaddress.ip_address(ip.strip())
    except ValueError:
        return "unknown"
    if isinstance(addr, ipaddress.IPv4Address):
        return str(ipaddress.ip_network(f"{addr}/24", strict=False).network_address)
    return str(ipaddress.ip_network(f"{addr}/48", strict=False).network_address)


def _hash_ip(ip: str | None) -> str:
    """Hash the COARSENED IP with the SECRET_KEY as salt.

    Coarsening happens before hashing so the rotating-egress problem is
    solved at the input layer (code-review D1).
    """
    bucket = _coarsen_ip(ip)
    raw = f"{settings.SECRET_KEY}:{bucket}".encode()
    return hashlib.sha256(raw).hexdigest()[:16]


def _ttl_seconds() -> int:
    return int(getattr(settings, "MFA_SESSION_TTL_SECONDS", 300))


def issue(*, user: User, stage: Stage, ip: str | None) -> str:
    """Mint a fresh `mfa_session` token bound to `user`, `stage`, and `ip`."""
    payload = {
        "sub": user.id,
        "stage": stage,
        "ip_hash": _hash_ip(ip),
        "jti": secrets.token_urlsafe(16),
    }
    signer = TimestampSigner(salt=_SIGNER_SALT)
    return signer.sign(json.dumps(payload, separators=(",", ":")))


def verify(*, token: str, request_ip: str | None, expected_stage: Stage) -> User:
    """Verify a token: signature valid, not expired, IP bucket matches, not
    blacklisted, `stage` matches the caller's expectation, payload is a
    well-formed dict with the expected fields.
    """
    signer = TimestampSigner(salt=_SIGNER_SALT)
    try:
        raw = signer.unsign(token, max_age=_ttl_seconds())
    except SignatureExpired as exc:
        raise MfaSessionExpired() from exc
    except BadSignature as exc:
        raise MfaSessionInvalid() from exc

    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, ValueError) as exc:
        raise MfaSessionInvalid() from exc

    # Code-review P9 — defensive against `json.loads` returning a non-dict
    # (`null`, list, scalar). Without this, `.get()` raises `AttributeError`
    # and the request 500s instead of returning a clean 400.
    if not isinstance(payload, dict):
        raise MfaSessionInvalid()

    if payload.get("stage") != expected_stage:
        raise MfaSessionInvalid()
    if payload.get("ip_hash") != _hash_ip(request_ip):
        raise MfaSessionInvalid()

    jti = payload.get("jti")
    if not isinstance(jti, str) or not jti.strip():
        raise MfaSessionInvalid()

    # Code-review P15 — distinct `MfaSessionConsumed` so the frontend can
    # route to "go back and reconnect, your previous attempt already
    # succeeded" instead of the generic "invalid".
    if cache.get(f"{_BLACKLIST_KEY_PREFIX}{jti}"):
        raise MfaSessionConsumed()

    sub = payload.get("sub")
    if not isinstance(sub, str):
        # Defensive: prevent ValueError/TypeError from User.objects.filter(pk=...)
        # with a non-string pk that would bubble up as 500.
        raise MfaSessionInvalid()
    user = User.objects.filter(pk=sub).first()
    if user is None:
        raise MfaSessionInvalid()
    return user


def consume(*, token: str) -> None:
    """Mark this token as used — subsequent `verify()` calls refuse it.

    Best-effort: cache exceptions are caught + logged (code-review P8).
    Strict TTL match (code-review P10) — expired tokens cannot be
    blacklisted post-hoc.
    """
    signer = TimestampSigner(salt=_SIGNER_SALT)
    try:
        raw = signer.unsign(token, max_age=_ttl_seconds())
    except (BadSignature, SignatureExpired):
        return
    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return
    if not isinstance(payload, dict):
        return
    jti = payload.get("jti")
    if not isinstance(jti, str) or not jti.strip():
        return
    try:
        cache.set(f"{_BLACKLIST_KEY_PREFIX}{jti}", "1", timeout=_ttl_seconds())
    except Exception:
        log.warning("mfa_session.consume.cache_failed", jti_prefix=jti[:8], exc_info=True)


def _extract_jti(token: str) -> str | None:
    """Best-effort JTI extraction for the failure / use counters."""
    signer = TimestampSigner(salt=_SIGNER_SALT)
    try:
        raw = signer.unsign(token, max_age=_ttl_seconds())
        payload = json.loads(raw)
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    jti = payload.get("jti")
    return jti if isinstance(jti, str) and jti.strip() else None


def record_failure(*, token: str) -> int:
    """Bump the per-token failure counter; blacklist the JTI on the
    `MAX_FAILS_PER_TOKEN`-th failure (code-review P28).

    Returns the post-increment counter value. Best-effort against Redis
    outages — a cache failure leaves the counter at 0 but does NOT block
    the login flow.
    """
    jti = _extract_jti(token)
    if not jti:
        return 0
    key = f"{_FAIL_COUNTER_KEY_PREFIX}{jti}"
    try:
        cache.add(key, 0, timeout=_ttl_seconds())
        count = cache.incr(key)
    except Exception:
        log.warning("mfa_session.record_failure.cache_failed", jti_prefix=jti[:8], exc_info=True)
        return 0

    if count >= MAX_FAILS_PER_TOKEN:
        try:
            cache.set(f"{_BLACKLIST_KEY_PREFIX}{jti}", "1", timeout=_ttl_seconds())
        except Exception:
            log.warning(
                "mfa_session.record_failure.blacklist_failed",
                jti_prefix=jti[:8],
                exc_info=True,
            )
    return count


def record_use(*, token: str) -> int:
    """Bump the per-token use counter for the enroll/start endpoint
    (code-review P1). Blacklists the JTI on the `MAX_USES_PER_TOKEN`-th
    call so a stolen token can't be replayed indefinitely.

    The challenge / enroll-confirm endpoints already consume the JTI on
    SUCCESS; this counter is specifically for the enroll/start endpoint
    which is replay-friendly by spec design (the user may re-scan the QR).
    """
    jti = _extract_jti(token)
    if not jti:
        return 0
    key = f"{_USE_COUNTER_KEY_PREFIX}{jti}"
    try:
        cache.add(key, 0, timeout=_ttl_seconds())
        count = cache.incr(key)
    except Exception:
        log.warning("mfa_session.record_use.cache_failed", jti_prefix=jti[:8], exc_info=True)
        return 0

    if count >= MAX_USES_PER_TOKEN:
        try:
            cache.set(f"{_BLACKLIST_KEY_PREFIX}{jti}", "1", timeout=_ttl_seconds())
        except Exception:
            log.warning(
                "mfa_session.record_use.blacklist_failed",
                jti_prefix=jti[:8],
                exc_info=True,
            )
    return count
