"""Path-Advisor accounts models — User (Story 1.3) + GdprExportRequest (Story 1.11) +
AccountDeletionRequest (Story 1.12 — right to erasure)."""

from __future__ import annotations

from datetime import timedelta
from typing import ClassVar

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from apps.accounts.managers import UserManager
from apps.core.ids import generate_id


def _default_user_id() -> str:
    return generate_id("usr")


def _default_gdpr_export_id() -> str:
    return generate_id("gex")


def _default_parental_consent_id() -> str:
    return generate_id("pcn")


def _default_parental_consent_expires_at() -> timezone.datetime:
    # 60-day window — matches the AC6 suspension job (Story 1.4 §AC1).
    return timezone.now() + timedelta(days=60)


def _default_account_deletion_id() -> str:
    return generate_id("adr")


def _default_account_deletion_hard_delete_after() -> timezone.datetime:
    # 30-day grace window (Story 1.12 §AC1). Imported lazily to avoid circular
    # import at module load — `settings` may need apps.accounts to be ready.
    from django.conf import settings

    days = getattr(settings, "GDPR_ACCOUNT_DELETION_GRACE_DAYS", 30)
    return timezone.now() + timedelta(days=days)


class UserRole(models.TextChoices):
    STUDENT = "student", "Élève"
    PARENT = "parent", "Parent"
    COUNSELOR = "counselor", "Conseiller"
    SCHOOL_ADMIN = "school_admin", "Administrateur école partenaire"
    PATH_ADMIN = "path_admin", "Administrateur Path-Advisor"
    # Story 1.7 §AC1 — 6th role per PRD §"Matrice RBAC". Support users handle
    # tickets with a MASKED profile + activity-journal view; no audit-log read,
    # no bulletins access without DPO escalation.
    SUPPORT = "support", "Support utilisateur"


class UserStatus(models.TextChoices):
    EMAIL_UNVERIFIED = "email_unverified", "Email non vérifié"
    PENDING_PARENTAL_CONSENT = "pending_parental_consent", "Consentement parental en attente"
    ACTIVE = "active", "Actif"
    SUSPENDED = "suspended", "Suspendu"
    DELETED = "deleted", "Supprimé"


class User(AbstractBaseUser, PermissionsMixin):
    id = models.CharField(
        primary_key=True,
        max_length=32,
        default=_default_user_id,
        editable=False,
    )
    email = models.EmailField(unique=True, db_index=True)

    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.STUDENT,
    )
    birth_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=30,
        choices=UserStatus.choices,
        default=UserStatus.EMAIL_UNVERIFIED,
    )

    email_verified_at = models.DateTimeField(null=True, blank=True)
    consent_rgpd_at = models.DateTimeField(null=True, blank=True)
    # null is semantically distinct from "" here: it marks accounts created before
    # the CGU/RGPD prompt was introduced (none today, but the column survives a
    # future schema change without a default migration).
    consent_cgu_version = models.CharField(max_length=20, null=True, blank=True)  # noqa: DJ001

    # Multi-tenant scope. Stays null for B2C accounts; populated for B2B users (Story 1.8 RLS).
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)  # soft delete (Story 1.12)
    # Story 1.5: per-account lockout after 5 failed logins in 15 min → set to
    # `now() + 10 min` by `login_security.record_failed_attempt` when the
    # threshold trips. Source of truth for the "locked" state (the Redis
    # counter that drives the threshold is the staging state — see Story 1.5
    # §AC4 + §4.5 #1 for the asymmetry rationale).
    locked_until = models.DateTimeField(null=True, blank=True, db_index=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: ClassVar[list[str]] = []

    class Meta:
        db_table = "users"
        indexes: ClassVar[list[models.Index]] = [
            models.Index(fields=["status"]),
            models.Index(fields=["role"]),
        ]

    def __str__(self) -> str:
        return self.email

    @property
    def is_email_verified(self) -> bool:
        return self.email_verified_at is not None

    @property
    def is_locked(self) -> bool:
        """True iff the user is currently locked out (Story 1.5 §AC4)."""
        return self.locked_until is not None and self.locked_until > timezone.now()

    @property
    def is_fully_active(self) -> bool:
        """True iff the user has verified their email AND, if a minor, the parent consented.

        Frontend gates "limited mode" on this flag (Story 1.4 §AC3 / AC7). Pending-consent
        students may have `email_verified_at` set but stay `pending_parental_consent`
        until the parent decides.
        """
        return self.email_verified_at is not None and self.status == UserStatus.ACTIVE

    @property
    def requires_mfa(self) -> bool:
        """True iff this user MUST go through the MFA challenge on every login.

        Two paths trigger it (Story 1.6 §AC1, §AC2, §AC3):
        - Role is in STAFF_ROLES_REQUIRING_MFA (FORCED by NFR-S2: counselor,
          school_admin, path_admin) — they MUST enroll on first login and
          challenge on every subsequent login.
        - User has already enrolled an `MfaProfile.enrolled_at` (B2C opt-in) —
          their own choice; challenges on every login from then on.
        """
        if self.role in STAFF_ROLES_REQUIRING_MFA:
            return True
        return self.has_mfa_enrolled

    @property
    def has_mfa_enrolled(self) -> bool:
        """True iff this user has a confirmed `MfaProfile.enrolled_at` timestamp.

        Distinct from `requires_mfa`: a fresh staff user (counselor with no
        profile yet) returns `requires_mfa=True, has_mfa_enrolled=False` →
        forced into the enrollment flow.

        Defensive against missing row: the OneToOne reverse-accessor raises
        `MfaProfile.DoesNotExist` (NOT AttributeError) when no row exists, so
        the bare `getattr(..., None)` pattern does NOT catch it. Use the
        explicit try/except idiom.
        """
        try:
            profile = self.mfa_profile
        except MfaProfile.DoesNotExist:
            return False
        return profile.enrolled_at is not None


#: Set of roles whose accounts MUST go through MFA on every login (NFR-S2).
#: B2C roles (`STUDENT`, `PARENT`) are NOT in this set — for them MFA is opt-in
#: via the `/parametres/securite/mfa` settings page.
STAFF_ROLES_REQUIRING_MFA = frozenset(
    {
        UserRole.COUNSELOR,
        UserRole.SCHOOL_ADMIN,
        UserRole.PATH_ADMIN,
    }
)


class MfaProfile(models.Model):
    """Per-user MFA state — Story 1.6.

    Single row per user (`OneToOneField`) tracking enrollment timestamp,
    last successful challenge, and the DPO-reset flag that forces re-enrollment
    on the next login (§AC7).

    The actual TOTP secret + recovery codes live in django-otp's tables
    (`otp_totp_totpdevice`, `otp_static_staticdevice`, `otp_static_statictoken`).
    This model is the Path-Advisor-specific metadata layer on top — django-otp
    has no equivalent of `enrolled_at` (it tracks `confirmed: bool` only) and
    no equivalent of the DPO reset flag.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="mfa_profile",
        primary_key=True,
    )
    enrolled_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=(
            "Set on successful `mfa.confirm_enrollment` — the moment the user "
            "first verified a TOTP code. Reset to NULL by DPO override."
        ),
    )
    last_challenge_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=(
            "Updated on every successful `mfa.verify_challenge`. Used by "
            "`recovery-codes/regenerate/` to enforce 'recent challenge' "
            "re-auth (cf. Story 1.6 §T5)."
        ),
    )
    requires_enrollment_at_next_login = models.BooleanField(
        default=False,
        help_text=(
            "Set to TRUE by `mfa.reset_by_dpo` (Story 1.6 §AC7). The next "
            "login forces the user through enrollment again, even though "
            "their `role` would normally only force enrollment on the very "
            "first login. Cleared on the next successful enrollment-confirm."
        ),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "accounts_mfa_profile"
        verbose_name = "MFA profile"
        verbose_name_plural = "MFA profiles"

    def __str__(self) -> str:
        state = "enrolled" if self.enrolled_at else "pending"
        return f"MfaProfile<{self.user_id}:{state}>"


class GdprExportStatus(models.TextChoices):
    PENDING = "pending", "En attente"
    IN_PROGRESS = "in_progress", "En cours"
    READY = "ready", "Prêt"
    EXPIRED = "expired", "Expiré"
    FAILED = "failed", "Échec"


class GdprExportRequest(models.Model):
    """User request to export their personal data (GDPR Article 20).

    Lifecycle: pending → in_progress → ready → expired (after GDPR_EXPORT_VALIDITY_DAYS).
    Failure path: pending → in_progress → failed (the quota does NOT consume on failure).

    The `user_id` is a logical FK (CharField, no DB constraint) so the export
    survives a hard-delete of the user account (Story 1.12) — a ready export
    remains downloadable for 7 days even if the user account is gone.
    """

    id = models.CharField(
        primary_key=True,
        max_length=32,
        default=_default_gdpr_export_id,
        editable=False,
    )
    user_id = models.CharField(max_length=32, db_index=True)
    status = models.CharField(
        max_length=20,
        choices=GdprExportStatus.choices,
        default=GdprExportStatus.PENDING,
        db_index=True,
    )

    requested_at = models.DateTimeField(auto_now_add=True, db_index=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ready_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    archive_s3_key = models.CharField(max_length=512, null=True, blank=True)  # noqa: DJ001
    manifest_s3_key = models.CharField(max_length=512, null=True, blank=True)  # noqa: DJ001
    archive_sha256 = models.CharField(max_length=64, null=True, blank=True)  # noqa: DJ001
    archive_size_bytes = models.BigIntegerField(null=True, blank=True)

    # Argon2 hash of the archive password (the cleartext password is sent in the
    # second email and NEVER persisted). Used to prove possession during DPO
    # incident handling — never re-displayed to the user.
    password_hash = models.CharField(max_length=128, null=True, blank=True)  # noqa: DJ001

    error_code = models.CharField(max_length=50, null=True, blank=True)  # noqa: DJ001
    error_message = models.TextField(null=True, blank=True)  # noqa: DJ001

    download_count = models.PositiveIntegerField(default=0)
    last_downloaded_at = models.DateTimeField(null=True, blank=True)

    # Idempotency guard for the "ready" email batch — once set, notify_export_ready
    # refuses to re-send. Cf. story §3.2 anti-pattern "don't re-send emails on
    # task replay".
    emails_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "gdpr_export_requests"
        ordering: ClassVar[list[str]] = ["-requested_at"]
        indexes: ClassVar[list[models.Index]] = [
            models.Index(
                fields=["user_id", "-requested_at"],
                name="idx_gdpr_exports_user_req",
            ),
            models.Index(
                fields=["status", "expires_at"],
                name="idx_gdpr_exports_status_exp",
            ),
        ]
        # Partial unique index — only one active (pending/in_progress) export
        # per user (post-review patch D4, 2026-05-24).
        constraints: ClassVar[list] = [
            models.UniqueConstraint(
                fields=["user_id"],
                condition=models.Q(status__in=("pending", "in_progress")),
                name="uniq_gdpr_active_per_user",
            ),
        ]

    def __str__(self) -> str:
        return f"GdprExportRequest({self.id}, user={self.user_id}, status={self.status})"

    @property
    def is_active(self) -> bool:
        """True if the request is being processed or is downloadable."""
        return self.status in (GdprExportStatus.PENDING, GdprExportStatus.IN_PROGRESS)

    @property
    def is_downloadable(self) -> bool:
        return self.status == GdprExportStatus.READY


class AccountDeletionRequest(models.Model):
    """User-initiated account deletion request — GDPR Article 17 (right to erasure).

    Lifecycle (Story 1.12):
        soft-delete (User.status = DELETED, is_active = False) at create time
        ───────── 30-day grace window ─────────
        cancel via /cancel/ endpoint OR DPO admin override ──► status restored
                              OR
        hard-delete sweep (`accounts.sweep_account_deletions`) ──► User.delete()
            cascades parental_consents, S3 prefixes purged, audit row written.

    The `user` FK uses `on_delete=models.SET_NULL` so the row survives the
    User cascade — it is itself an audit artifact (NFR-S4, 3-year retention).
    `user_id_snapshot` carries the original id past the SET_NULL so post-delete
    rows still answer "which user did this concern" without a join.
    """

    id = models.CharField(
        primary_key=True,
        max_length=32,
        default=_default_account_deletion_id,
        editable=False,
    )
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        related_name="deletion_requests",
        null=True,
        blank=True,
    )
    # Frozen at create time so the row survives the SET_NULL when hard-delete fires.
    # Indexed because the in-flight check (AC2) queries by this column when `user_id` may be NULL.
    user_id_snapshot = models.CharField(max_length=32, db_index=True)

    # `secrets.token_urlsafe(32)` → 43 base64 chars (256 bits of entropy); the
    # column is sized at 64 chars to leave room for future token schemes.
    cancel_token = models.CharField(max_length=64, unique=True, db_index=True)

    requested_at = models.DateTimeField(default=timezone.now, db_index=True)
    # Denormalised `requested_at + GDPR_ACCOUNT_DELETION_GRACE_DAYS` — keeps the
    # sweep query fast and immune to clock skew on the worker.
    hard_delete_after = models.DateTimeField(default=_default_account_deletion_hard_delete_after)

    cancelled_at = models.DateTimeField(null=True, blank=True)
    # Free-form, prefixed by source: `user_self_service:<reason?>` /
    # `dpo_override:<dpo_user_id>:<reason>` / `system:<reason>`. The DPO filter
    # in the audit playbook keys on the prefix.
    cancel_reason = models.CharField(max_length=200, null=True, blank=True)  # noqa: DJ001

    hard_deleted_at = models.DateTimeField(null=True, blank=True)
    # Cap on retry storms when the hard-delete step keeps failing (e.g. S3
    # outage). After GDPR_ACCOUNT_DELETION_MAX_HARD_DELETE_ATTEMPTS, the sweep
    # writes `gdpr.account_hard_delete_giving_up` and skips the row.
    hard_delete_attempt_count = models.PositiveSmallIntegerField(default=0)
    # Last failure surface for the DPO incident playbook — only the exception
    # CLASS NAME is stored (matches the Story 1.11 sanitisation pattern).
    last_failure_code = models.CharField(max_length=50, null=True, blank=True)  # noqa: DJ001

    # Forensic context — same shape as ParentalConsent's decision_* columns.
    requested_ip_truncated = models.CharField(max_length=45, null=True, blank=True)  # noqa: DJ001
    requested_user_agent = models.CharField(max_length=200, null=True, blank=True)  # noqa: DJ001

    # `make_password(submitted_password)` from the moment of request. Stored
    # for forensic continuity ("the user proved they knew this hash on this
    # date") — NEVER consulted as the cancel-time auth check (that one calls
    # `user.check_password` against the CURRENT hash; cf. story §4.5 #4).
    password_hash_at_request = models.CharField(max_length=128)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "account_deletion_requests"
        ordering: ClassVar[list[str]] = ["-requested_at"]
        indexes: ClassVar[list[models.Index]] = [
            # Sweep query: `cancelled_at IS NULL AND hard_deleted_at IS NULL AND hard_delete_after <= now`.
            models.Index(
                fields=["hard_delete_after", "cancelled_at", "hard_deleted_at"],
                name="idx_acct_del_sweep",
            ),
            # AC2 in-flight lookup by user (post-cascade rows have user=NULL so this
            # index complements the FK index without overlapping).
            models.Index(
                fields=["user_id_snapshot", "-requested_at"],
                name="idx_acct_del_user_req",
            ),
        ]
        # Partial unique index — only one in-flight deletion per user (mirrors
        # the GdprExportRequest pattern from Story 1.11). Two concurrent POSTs
        # both passing the application-level check fail-fast on this constraint.
        constraints: ClassVar[list] = [
            models.UniqueConstraint(
                fields=["user_id_snapshot"],
                condition=models.Q(cancelled_at__isnull=True, hard_deleted_at__isnull=True),
                name="uniq_acct_del_active_per_user",
            ),
        ]
        # Custom permission for the DPO override action (Story 1.12 §AC9). Grant
        # this on a per-user basis instead of relying on `is_superuser` so the
        # auditable identity stays sharp.
        permissions: ClassVar[list[tuple[str, str]]] = [
            ("cancel_deletion_request", "Can cancel an in-flight account-deletion request (DPO)"),
        ]

    def __str__(self) -> str:
        state = "pending"
        if self.hard_deleted_at:
            state = "hard_deleted"
        elif self.cancelled_at:
            state = "cancelled"
        return f"AccountDeletionRequest({self.id}, user={self.user_id_snapshot}, state={state})"

    @property
    def is_pending(self) -> bool:
        return self.cancelled_at is None and self.hard_deleted_at is None

    @property
    def is_past_grace_window(self) -> bool:
        return self.hard_delete_after <= timezone.now()


class ParentalConsentDecision(models.TextChoices):
    GRANTED = "granted", "Autorisé"
    REFUSED = "refused", "Refusé"


class ParentalConsent(models.Model):
    """Pending or resolved parental authorization for a < 15-year-old student (Story 1.4).

    The parent has no Path-Advisor account at decision time — the URL-safe `token`
    IS the authentication for the single decision moment (cf. ADR-0003). Once Epic 6
    ships parent accounts, `parent_user_id` may be backfilled to link the two.
    """

    id = models.CharField(
        primary_key=True,
        max_length=32,
        default=_default_parental_consent_id,
        editable=False,
    )
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="parental_consents",
    )
    parent_email = models.EmailField()
    # Backfilled when Epic 6 ships parent self-service accounts; null otherwise.
    # NULL vs "" carries meaning here: NULL = anonymous parent (no PA account).
    parent_user_id = models.CharField(max_length=32, null=True, blank=True, db_index=True)  # noqa: DJ001
    # Denormalized from `student.tenant_id` so the RLS policy on `parental_consents`
    # can filter without joining (Story 1.8). Auto-synced on first save (see `save()`
    # below). NULL for B2C students.
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    # `secrets.token_urlsafe(32)` → 43 base64 chars; 64 max leaves room for future schemes.
    token = models.CharField(max_length=64, unique=True, db_index=True)
    requested_at = models.DateTimeField(default=timezone.now)
    # Denormalized `requested_at + 60 days` — keeps the AC6 suspension query fast and
    # protects against clock skew on the worker that runs the Celery beat job.
    expires_at = models.DateTimeField(default=_default_parental_consent_expires_at)
    reminder_sent_at = models.DateTimeField(null=True, blank=True)
    # NULL is the pending state; "granted"/"refused" are the decided states.
    decision = models.CharField(  # noqa: DJ001
        max_length=10,
        choices=ParentalConsentDecision.choices,
        null=True,
        blank=True,
    )
    decided_at = models.DateTimeField(null=True, blank=True)
    # Story 1.4 review §P26 (D1): client-supplied `accepted_at` from the parent's
    # browser. Stored alongside the server-authoritative `decided_at` so a future
    # forensic audit can compare clock drift / detect tampered clients. Validated
    # against `decided_at` with ±5 min skew tolerance at write time.
    client_accepted_at = models.DateTimeField(null=True, blank=True)
    # Story 1.4 review §P14: tracks whether the "granted" email made it out of SMTP.
    # The reconciliation task `accounts.notify_unconfirmed_granted_consents` retries
    # rows with `decision='granted' AND notification_sent_at IS NULL`.
    notification_sent_at = models.DateTimeField(null=True, blank=True)
    # SHA-256 hex from the 8-field ConsentDialog payload (Story 1.14 review) — proves
    # exactly what content the parent saw at decision time. NULL until decision lands.
    content_hash = models.CharField(max_length=64, null=True, blank=True)  # noqa: DJ001
    # Forensic decision context — never the plain parent_email (that's hashed into the
    # audit log to comply with data minimization; cf. Story 1.4 §AC4).
    decision_ip_truncated = models.CharField(max_length=45, null=True, blank=True)  # noqa: DJ001
    decision_user_agent = models.CharField(max_length=200, null=True, blank=True)  # noqa: DJ001
    # Story 1.9 §AC1 — set by Story 1.10 on user-initiated revocation. The
    # access-list query filters `revoked_at IS NULL` so only live grants show.
    revoked_at = models.DateTimeField(null=True, blank=True)
    # Story 1.10 review D5 — gates `notify_parental_consent_revoked` so a
    # Celery retry can't re-deliver the same email. Distinct from
    # `notification_sent_at` (Story 1.4 granted email).
    revocation_notification_sent_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "parental_consents"
        indexes: ClassVar[list[models.Index]] = [
            # Supports the Celery beat queries `decision IS NULL AND requested_at < cutoff`.
            models.Index(fields=["decision", "requested_at"]),
            models.Index(fields=["decision", "expires_at"]),
            # Supports the "find latest pending consent for student" lookup used by /resend/.
            models.Index(fields=["student", "decision"]),
            # Story 1.9 — supports the access-list query
            # `student=:u AND decision='granted' AND revoked_at IS NULL`.
            models.Index(fields=["student", "revoked_at"], name="parental_co_student_revoke_idx"),
        ]

    def __str__(self) -> str:
        return f"ParentalConsent(student={self.student_id} decision={self.decision or 'pending'})"

    def save(self, *args: object, **kwargs: object) -> None:
        # Story 1.8: keep `tenant_id` consistent with the student's tenant so
        # the RLS policy can filter without joining. Only auto-fill on first
        # save / when missing — explicit caller overrides win.
        if self.tenant_id is None and self.student_id:
            student_tenant = (
                type(self)
                .student.field.related_model.objects.filter(
                    pk=self.student_id,
                )
                .values_list("tenant_id", flat=True)
                .first()
            )
            self.tenant_id = student_tenant
        super().save(*args, **kwargs)  # type: ignore[misc]

    @property
    def is_pending(self) -> bool:
        return self.decision is None

    @property
    def is_expired(self) -> bool:
        # Inclusive of the boundary: an `expires_at` equal to `now()` is past the
        # 60-day window. Story 1.4 review §P19 — eliminates a 1-second loophole.
        return self.expires_at <= timezone.now()
