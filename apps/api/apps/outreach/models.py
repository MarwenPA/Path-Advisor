"""Early-outreach request model — Stories 5.4 + 5.5 + 5.6 + 5.7.

`EarlyOutreachRequest` is the central model for the rest of Epic 5 (5.8
real-time stat propagation, 5.9 enriched history).

Story 5.5 adds a moderation gate on the optional motivation: a request with
a non-empty `motivation_text` starts life as `pending_moderation` instead of
`pending`, and stays blocked (not visible/sendable to a school) until a
`path_admin` approves it (→ back to `pending`) or rejects it (→ `rejected`,
with `rejection_reason` set — the student can then resubmit).

Story 5.6 gave schools their own accounts (`SchoolStaff`, apps.schools) and
a read-only reception queue, scoped to their own school.

Story 5.7 adds `EarlyOutreachResponse` — the school's answer to a request
(one of 3 actions: intéressant / non aligné / demande d'entretien), which
flips the request to `responded`. Recomputing the student's admission stat
from that response is explicitly Story 5.8's job, not this model's.

Data classification: contains a student's motivation text + which school/
profession they're targeting — not health data, but personal/behavioral.
No RLS today (neither side of this relationship is tenant-scoped — B2C
student, global-reference school); the school-side tenant boundary is
enforced at the application layer (`apps.outreach.services.
school_reception`, `bypass_rls`-wrapped after scoping), not via RLS.
"""

from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.core.ids import generate_id


def _default_outreach_id() -> str:
    return generate_id("reach")


class EarlyOutreachRequestStatus(models.TextChoices):
    PENDING = "pending", "En attente"
    PENDING_MODERATION = "pending_moderation", "Motivation en cours de relecture"
    REJECTED = "rejected", "Motivation refusée"
    RESPONDED = "responded", "École a répondu"
    EXPIRED_7D = "expired_7d", "Expiré (7 jours sans réponse)"


class EarlyOutreachRequest(models.Model):
    """One "envoi anticipé" — a student sending their profile to one school."""

    id = models.CharField(
        default=_default_outreach_id,
        editable=False,
        max_length=32,
        primary_key=True,
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="early_outreach_requests",
    )
    school = models.ForeignKey(
        "schools.School",
        on_delete=models.CASCADE,
        related_name="early_outreach_requests",
    )
    # "Métier visé" — chosen by the student among THEIR OWN recommendations,
    # never a free-form pick (AC2, §2 scope decision).
    profession = models.ForeignKey(
        "professions.Profession",
        on_delete=models.PROTECT,
        related_name="early_outreach_requests",
    )
    # "Parcours sélectionné" — resolved server-side (the default Parcours
    # for profession+school if one exists), never a manual UI choice
    # (§2 scope decision, keeps the Sheet simple). Nullable: not every
    # profession/school pair has a matching Parcours row.
    parcours = models.ForeignKey(
        "schools.Parcours",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="early_outreach_requests",
    )
    motivation_text = models.TextField(
        blank=True,
        help_text=(
            "Optional free-text motivation, 200-500 words when present "
            "(Story 5.5). Gates the request into `pending_moderation` until "
            "a path_admin approves/rejects it."
        ),
    )
    status = models.CharField(
        max_length=20,
        choices=EarlyOutreachRequestStatus.choices,
        default=EarlyOutreachRequestStatus.PENDING,
    )
    #: Story 9.4 — the AC's typed rejection (contenu inapproprié, données
    #: tierces, discrimination, autre) on top of the free-text reason.
    rejection_category = models.CharField(
        max_length=30,
        blank=True,
        default="",
        choices=[
            ("contenu_inapproprie", "Contenu inapproprié"),
            ("donnees_tierces", "Données personnelles de tiers"),
            ("discrimination", "Discrimination"),
            ("autre", "Autre"),
        ],
    )
    rejection_reason = models.TextField(
        blank=True,
        help_text="Set when `status=rejected` — explains why to the student (Story 5.5 AC).",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "early_outreach_requests"
        ordering = ["-created_at"]
        indexes = [
            # Backs the monthly-quota COUNT query (student, created_at range).
            models.Index(fields=["student", "created_at"]),
        ]

    def __str__(self) -> str:  # pragma: no cover - debug helper
        return f"EarlyOutreachRequest({self.id}, {self.student_id} -> {self.school_id})"


class EarlyOutreachResponseAction(models.TextChoices):
    INTERESTED = "interested", "Profil intéressant"
    NOT_ALIGNED = "not_aligned", "Profil non aligné"
    INTERVIEW_REQUESTED = "interview_requested", "Demande d'entretien"


def _default_response_id() -> str:
    return generate_id("resp")


class EarlyOutreachResponse(models.Model):
    """The school's answer to one `EarlyOutreachRequest` — Story 5.7.

    One row per request (`OneToOne` — a school responds once; there's no
    "change my mind" flow in the MVP). `proposed_slots`/`accepted_slot`/
    `alternative_note` only apply to `INTERVIEW_REQUESTED`; they stay empty
    for the other two actions.

    Propagating this to the student's admission stat (+10/+20, +5/+10,
    -10/-20 points per the epic's own numbers) is Story 5.8's job — this
    model only records the school's decision.
    """

    id = models.CharField(
        default=_default_response_id, editable=False, max_length=32, primary_key=True
    )
    request = models.OneToOneField(
        EarlyOutreachRequest,
        on_delete=models.CASCADE,
        related_name="response",
    )
    action = models.CharField(max_length=30, choices=EarlyOutreachResponseAction.choices)
    # "Commentaire pour l'élève" — optional, ≤200 words (validated in the
    # serializer). §2 scope decision: NOT gated through the a-priori
    # moderation queue Story 5.5 built for the student's motivation — a
    # school's response needs to reach the student promptly (the epic's own
    # "5 min" propagation promise), and the abuse surface is much smaller
    # (few dozen partner-school staff accounts, onboarded manually, vs.
    # thousands of students). Visible to a path_admin after the fact via
    # the Django admin for reactive moderation if ever needed.
    comment = models.TextField(blank=True)
    # Only for INTERVIEW_REQUESTED — 2-3 ISO-8601 datetime strings the
    # school proposes.
    proposed_slots = models.JSONField(default=list, blank=True)
    # Set once the student accepts one of `proposed_slots` (verbatim, not
    # re-validated against the list at read time — the accept endpoint
    # enforces membership at write time).
    accepted_slot = models.CharField(max_length=40, blank=True)
    # Set if the student can't make any proposed slot and proposes a
    # free-text alternative instead of a 2nd negotiation round (§2 scope
    # decision — a full back-and-forth scheduling negotiation is out of
    # scope for the MVP; the school follows up externally, per the epic's
    # own "visio externe en MVP" framing).
    alternative_note = models.TextField(blank=True)

    #: Story 9.4 (amendement revue Epic 8, P2-5) — a non-empty free-text
    #: comment from school staff enters A PRIORI moderation before a minor
    #: ever sees it: the response email leaves immediately WITHOUT the
    #: comment; in-app, the comment only appears once approved. Empty
    #: comments are auto-approved (nothing to moderate).
    class CommentStatus(models.TextChoices):
        APPROVED = "approved", "Approuvé"
        PENDING = "pending", "En attente de modération"
        REJECTED = "rejected", "Rejeté"

    comment_status = models.CharField(
        max_length=12, choices=CommentStatus.choices, default=CommentStatus.APPROVED
    )
    comment_moderated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    comment_moderated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "early_outreach_responses"
        verbose_name = "Early Outreach Response"
        verbose_name_plural = "Early Outreach Responses"

    def __str__(self) -> str:  # pragma: no cover - debug helper
        return f"EarlyOutreachResponse({self.id}, {self.request_id}, {self.action})"


def _default_meeting_id() -> str:
    return generate_id("meet")


def _default_room_slug() -> str:
    # Unguessable Jitsi-style room: the URL is the only credential —
    # 16 bytes urlsafe ≈ 128 bits, préfixé pour l'hygiène côté instance.
    import secrets

    return f"path-advisor-{secrets.token_urlsafe(16)}"


class InterviewMeeting(models.Model):
    """Story 10.4 — le RDV visio né de l'acceptation d'un créneau (5.7).

    OneToOne sur la demande (une réponse = un entretien au plus, comme
    `EarlyOutreachResponse`). `scheduled_at` est le créneau accepté TYPÉ
    (les slots 5.7 restent des chaînes ISO — consigné) ; `room_slug` porte
    le lien visio (instance Jitsi via `settings.VISIO_BASE_URL`, transit
    only : Path-Advisor ne stocke ni flux ni enregistrement — AC3).

    `reminder_24h_sent_at` / `reminder_1h_sent_at` sont les colonnes de
    claim du beat de rappel (patron milestone 8.3 : UPDATE conditionnel,
    exactement-une-fois ; un ETA Redis > 4 h serait redélivré —
    `visibility_timeout`).

    Pas de RLS : comme le reste d'outreach, la frontière est applicative
    (deux parties — élève et staff école — qu'un RLS mono-owner ne sait
    pas exprimer), consigné.
    """

    id = models.CharField(
        primary_key=True, max_length=32, default=_default_meeting_id, editable=False
    )
    outreach = models.OneToOneField(
        EarlyOutreachRequest, on_delete=models.CASCADE, related_name="meeting"
    )
    scheduled_at = models.DateTimeField(db_index=True)
    room_slug = models.CharField(max_length=64, unique=True, default=_default_room_slug)
    reminder_24h_sent_at = models.DateTimeField(null=True, blank=True)
    reminder_1h_sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "interview_meetings"

    def __str__(self) -> str:  # pragma: no cover — debug nicety
        return f"InterviewMeeting({self.id}, {self.scheduled_at:%Y-%m-%d %H:%M})"

    @property
    def visio_url(self) -> str:
        from django.conf import settings as django_settings

        return f"{django_settings.VISIO_BASE_URL.rstrip('/')}/{self.room_slug}"
