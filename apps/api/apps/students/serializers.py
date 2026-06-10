"""Serializers for the onboarding step-1 endpoints (Story 2.1 AC5).

`OnboardingStep1ReadSerializer` shapes the GET response.

`OnboardingStep1PatchSerializer` accepts the partial PATCH payload
(`{step, passions?, valeurs?, interets?}`) and validates each sub-step
field against the curated referential
(`apps.students.onboarding.referentials`). Cross-language sync with the
frontend Zod schema is enforced by `tests/test_referentials.py`.

Validation philosophy:
- ABSENT field → not part of this PATCH, untouched in the model.
- PRESENT field → fully validated against the referential (defense in
  depth on top of the frontend Zod check). Reject on any unknown ID.

We also reject the catch-all "PATCH everything at once" usage that AC5
forbids: a single PATCH carries exactly one sub-step (`step` enum) plus
its corresponding payload. Mixing fields across sub-steps is rejected so
the frontend cannot silently submit an out-of-band shape that the UX
state machine doesn't model.
"""

from __future__ import annotations

from typing import Any

from rest_framework import serializers

from apps.students.models import OnboardingStep1Status, StudentProfile
from apps.students.onboarding.referentials import (
    MIN_PASSIONS,
    MIN_VALEURS,
    validate_interets_record,
    validate_passions_array,
    validate_valeurs_array,
)


# --- Read ------------------------------------------------------------------


class OnboardingStep1ReadSerializer(serializers.ModelSerializer):
    """GET shape — matches the frontend Zod expectation in `useOnboardingStep1`.

    Returns `null` for `onboarding_step1_completed_at` if step 1 is still
    in progress, otherwise an ISO-8601 timestamp.
    """

    class Meta:
        model = StudentProfile
        fields = (
            "passions",
            "valeurs",
            "interets",
            "onboarding_step1_status",
            "onboarding_step1_completed_at",
        )
        read_only_fields = fields


# --- PATCH -----------------------------------------------------------------


class OnboardingStep1PatchSerializer(serializers.Serializer):
    """Partial-update payload for one sub-step at a time (AC5).

    The `step` discriminator selects which other field must be present:
      - step=passions  → `passions: list[str]`
      - step=valeurs   → `valeurs: list[str]`
      - step=interets  → `interets: {"1": str|null, "2": ..., "3": ...}`

    The two skip paths (AC7) come through a dedicated `step=skip` payload
    that takes no other field but sets the status to `skipped` (or
    `partial_skipped` if the profile already has partial data).
    """

    STEP_CHOICES = (
        ("passions", "passions"),
        ("valeurs", "valeurs"),
        ("interets", "interets"),
        ("skip", "skip"),
    )

    step = serializers.ChoiceField(choices=STEP_CHOICES)
    passions = serializers.ListField(child=serializers.CharField(), required=False, allow_empty=True)
    valeurs = serializers.ListField(child=serializers.CharField(), required=False, allow_empty=True)
    interets = serializers.DictField(
        child=serializers.CharField(allow_null=True, allow_blank=True, required=False),
        required=False,
    )

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        step = attrs["step"]

        # Reject mixed sub-step payloads — only the discriminator's field is
        # allowed alongside `step`. Drops accidental "PATCH everything" calls
        # that would bypass the UX state machine.
        allowed_field = {
            "passions": "passions",
            "valeurs": "valeurs",
            "interets": "interets",
            "skip": None,
        }[step]
        other_fields = {"passions", "valeurs", "interets"} - {allowed_field} if allowed_field else {
            "passions",
            "valeurs",
            "interets",
        }
        offenders = other_fields & attrs.keys()
        if offenders:
            raise serializers.ValidationError(
                f"Step '{step}' does not accept fields {sorted(offenders)}."
            )

        if step == "passions":
            self._validate_passions(attrs.get("passions"))
        elif step == "valeurs":
            self._validate_valeurs(attrs.get("valeurs"))
        elif step == "interets":
            self._validate_interets(attrs.get("interets"))

        return attrs

    @staticmethod
    def _validate_passions(values: list[str] | None) -> None:
        if values is None:
            raise serializers.ValidationError({"passions": "Required for step 'passions'."})
        ok, err = validate_passions_array(values)
        if not ok:
            raise serializers.ValidationError({"passions": err})
        if 0 < len(values) < MIN_PASSIONS:
            # Mid-typing PATCH is allowed (sub-step Continue gates on this),
            # but if the user submits non-empty with <3 it's a frontend bug.
            raise serializers.ValidationError(
                {"passions": f"At least {MIN_PASSIONS} passions required when non-empty."}
            )

    @staticmethod
    def _validate_valeurs(values: list[str] | None) -> None:
        if values is None:
            raise serializers.ValidationError({"valeurs": "Required for step 'valeurs'."})
        ok, err = validate_valeurs_array(values)
        if not ok:
            raise serializers.ValidationError({"valeurs": err})
        if 0 < len(values) < MIN_VALEURS:
            raise serializers.ValidationError(
                {"valeurs": f"At least {MIN_VALEURS} valeurs required when non-empty."}
            )

    @staticmethod
    def _validate_interets(record: dict[str, str | None] | None) -> None:
        if record is None:
            raise serializers.ValidationError({"interets": "Required for step 'interets'."})
        # Normalize empty-string → None for the all-empty allowed case.
        normalized: dict[str, str | None] = {
            k: (None if (v is None or v.strip() == "") else v) for k, v in record.items()
        }
        ok, err = validate_interets_record(normalized)
        if not ok:
            raise serializers.ValidationError({"interets": err})

    # --- application ----------------------------------------------------

    def apply(self, profile: StudentProfile) -> StudentProfile:
        """Apply the validated payload to the profile. Caller saves.

        Pass 1 review H2 + H3 — the previous version called
        `profile.mark_completed()` unconditionally on `step=interets`, even
        when the profile carried zero passions / zero valeurs OR was
        already in a terminal state (`skipped` / `partial_skipped`). That
        let a single PATCH bypass the AC2 / AC3 minimums AND silently
        flipped a prior skip into a completion — breaking the AC7 distinction
        Story 2.7 (maturité de profil) depends on. The fixed branch
        explicitly checks both invariants before mutating status.
        """
        from apps.students.models import OnboardingStep1Status as Status
        from apps.students.onboarding.referentials import MIN_PASSIONS, MIN_VALEURS

        data = self.validated_data
        step = data["step"]

        # H2 — refuse any sub-step write on a terminal-state profile. The
        # frontend (AC10) already redirects users away from /step-1 when the
        # status is `completed`, but a stale tab or a non-browser client
        # could still hit the endpoint. Returning 409 keeps the audit trail
        # crisp ("client tried to mutate a closed onboarding") vs silently
        # over-writing the row.
        terminal_states = {Status.COMPLETED, Status.SKIPPED, Status.PARTIAL_SKIPPED}
        if profile.onboarding_step1_status in terminal_states and step != "skip":
            # `step=skip` is allowed against a terminal state (idempotent —
            # a second skip just refreshes the timestamp via mark_skipped).
            raise serializers.ValidationError(
                {
                    "step": (
                        f"Onboarding step 1 is already in terminal state "
                        f"'{profile.onboarding_step1_status}'. Submit `step=skip` "
                        f"to reaffirm or use the profile-edit endpoint (Story 2.6) "
                        f"to modify saved selections."
                    )
                },
                code="onboarding_step1_terminal",
            )

        if step == "passions":
            profile.passions = data["passions"]
            self._touch_in_progress(profile)
        elif step == "valeurs":
            profile.valeurs = data["valeurs"]
            self._touch_in_progress(profile)
        elif step == "interets":
            # Normalize once more at write time — caller may have given us
            # blank strings that we want stored as null.
            profile.interets = {
                k: (None if (v is None or v.strip() == "") else v)
                for k, v in data["interets"].items()
            }
            # H3 — completion requires BOTH AC2 (≥ MIN_PASSIONS) and AC3
            # (≥ MIN_VALEURS) satisfied. Without this guard a malicious or
            # buggy client could send `step=interets` with empty fields
            # against a fresh profile and immediately mark the row
            # `completed` — the recommendation engine (Epic 3) would then
            # consume a zero-signal row. If the minimums aren't met, the
            # status routes to `partial_skipped` (Story 2.7 distinguishes
            # this from a clean `completed`) and the interets payload is
            # still persisted so the user doesn't lose what they typed.
            passions_count = len(profile.passions or [])
            valeurs_count = len(profile.valeurs or [])
            if passions_count >= MIN_PASSIONS and valeurs_count >= MIN_VALEURS:
                profile.mark_completed()
            else:
                profile.mark_skipped(partial=True)
        elif step == "skip":
            has_partial = bool(profile.passions) or bool(profile.valeurs) or any(
                profile.interets.values()
            )
            profile.mark_skipped(partial=has_partial)

        return profile

    @staticmethod
    def _touch_in_progress(profile: StudentProfile) -> None:
        """Move pending → in_progress; preserve completed/skipped if already there."""
        if profile.onboarding_step1_status == OnboardingStep1Status.PENDING:
            profile.onboarding_step1_status = OnboardingStep1Status.IN_PROGRESS
