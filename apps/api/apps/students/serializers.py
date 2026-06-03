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
        """Apply the validated payload to the profile. Caller saves."""
        data = self.validated_data
        step = data["step"]

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
            # 1C is the last sub-step → completion (AC4).
            profile.mark_completed()
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
