"""Serializers for the onboarding endpoints (Stories 2.1 + 2.2).

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

from apps.students.models import (
    OnboardingStep1Status,
    OnboardingStep2Status,
    StudentLevelProfile,
    StudentProfile,
)
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

        # H2 — refuse any sub-step write on a TRULY terminal-state profile.
        # The frontend (AC10) already redirects users away from /step-1 when
        # the status is `completed`, but a stale tab or a non-browser client
        # could still hit the endpoint.
        #
        # Pass 2 PR2-H2 — only `completed` is genuinely terminal. `skipped` /
        # `partial_skipped` mean the user dropped off mid-flight; they MUST
        # be able to come back and finish later (this is the whole point of
        # the per-skip distinction Story 2.7 leverages). The Pass 1 fix
        # included those two in the terminal set, which combined with the
        # H3 routing-to-`partial_skipped` created a one-way dead-end: a
        # mis-clicked Terminer locked the user out of step-1 forever.
        # Now only `completed` blocks further sub-step writes.
        if profile.onboarding_step1_status == Status.COMPLETED and step != "skip":
            raise serializers.ValidationError(
                {
                    "step": (
                        "Onboarding step 1 is already completed. Use the "
                        "profile-edit endpoint (Story 2.6) to modify saved "
                        "selections."
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
            # Pass 2 PR2-H5 — a `step=skip` PATCH against a row that is
            # already `completed` must be a true no-op, NOT a regression to
            # `skipped`. The Pass 1 H2 fix exempted `step=skip` from the
            # terminal-state guard to keep skip idempotent; without this
            # additional check, a stale tab firing skip after a successful
            # completion would silently demote `completed` → `skipped`,
            # corrupting the maturité-de-profil signal Story 2.7 reads.
            if profile.onboarding_step1_status == Status.COMPLETED:
                return profile
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


# ---------------------------------------------------------------------------
# Step-2 serializers (Story 2.2)
# ---------------------------------------------------------------------------


class OnboardingStep2ReadSerializer(serializers.ModelSerializer):
    """GET /api/v1/students/me/onboarding/level response shape."""

    class Meta:
        model = StudentLevelProfile
        fields = [
            "level",
            "filiere",
            "sous_filiere_techno",
            "specialites",
            "intended_track",
            "postbac_year",
            "postbac_formation_type",
            "onboarding_step2_status",
            "onboarding_step2_completed_at",
            "level_ref_version",
        ]


class OnboardingStep2PatchSerializer(serializers.Serializer):
    """PATCH /api/v1/students/me/onboarding/level.

    Accepts a partial payload during editing (draft saves) or a full commit
    payload when `commit=true`. The full validation matrix (Story 2.2 §4.5)
    is enforced only when `commit=true`. Partial PATCHes only validate the
    fields that are present.
    """

    # Whether this is a final commit (récap → step-3) or a draft save
    commit = serializers.BooleanField(default=False)

    level = serializers.CharField(max_length=20, required=False, allow_null=True)
    filiere = serializers.CharField(max_length=10, required=False, allow_null=True)
    sous_filiere_techno = serializers.CharField(
        max_length=10, required=False, allow_null=True
    )
    specialites = serializers.ListField(
        child=serializers.CharField(), required=False, allow_empty=True
    )
    intended_track = serializers.CharField(
        max_length=15, required=False, allow_null=True
    )
    postbac_year = serializers.CharField(max_length=15, required=False, allow_null=True)
    postbac_formation_type = serializers.CharField(
        max_length=25, required=False, allow_null=True
    )
    skip = serializers.BooleanField(default=False)
    level_ref_version = serializers.CharField(
        max_length=20, required=False, allow_null=True
    )

    def validate_level(self, value: str | None) -> str | None:
        from apps.students.onboarding.levels import NIVEAU_IDS

        if value is not None and value not in NIVEAU_IDS:
            raise serializers.ValidationError(
                f"Unknown level '{value}'. Valid values: {sorted(NIVEAU_IDS)}"
            )
        return value

    def validate_filiere(self, value: str | None) -> str | None:
        from apps.students.onboarding.levels import FILIERE_IDS

        if value is not None and value not in FILIERE_IDS:
            raise serializers.ValidationError(
                f"Unknown filiere '{value}'. Valid values: {sorted(FILIERE_IDS)}"
            )
        return value

    def validate_sous_filiere_techno(self, value: str | None) -> str | None:
        from apps.students.onboarding.levels import SOUS_FILIERE_IDS

        if value is not None and value not in SOUS_FILIERE_IDS:
            raise serializers.ValidationError(
                f"Unknown sous_filiere_techno '{value}'."
            )
        return value

    def validate_intended_track(self, value: str | None) -> str | None:
        from apps.students.onboarding.levels import TRACK_3EME_IDS

        if value is not None and value not in TRACK_3EME_IDS:
            raise serializers.ValidationError(
                f"Unknown intended_track '{value}'."
            )
        return value

    def validate_postbac_year(self, value: str | None) -> str | None:
        from apps.students.onboarding.levels import POSTBAC_YEAR_IDS

        if value is not None and value not in POSTBAC_YEAR_IDS:
            raise serializers.ValidationError(f"Unknown postbac_year '{value}'.")
        return value

    def validate_postbac_formation_type(self, value: str | None) -> str | None:
        from apps.students.onboarding.levels import POSTBAC_FORMATION_IDS

        if value is not None and value not in POSTBAC_FORMATION_IDS:
            raise serializers.ValidationError(
                f"Unknown postbac_formation_type '{value}'."
            )
        return value

    def validate_specialites(self, value: list[str]) -> list[str]:
        from apps.students.onboarding.levels import SPECIALITE_IDS, SPECIALITE_PRO_IDS

        all_valid = SPECIALITE_IDS | SPECIALITE_PRO_IDS
        unknown = [s for s in value if s not in all_valid]
        if unknown:
            raise serializers.ValidationError(
                f"Unknown specialite IDs: {unknown}"
            )
        if len(value) != len(set(value)):
            raise serializers.ValidationError("Duplicate specialite IDs are not allowed.")
        return value

    def validate(self, data: dict) -> dict:
        """Full matrix validation (Story 2.2 §4.5) — only when commit=True."""
        if not data.get("commit"):
            return data

        from apps.students.onboarding.levels import (
            SPECIALITE_IDS,
            SPECIALITE_PRO_IDS,
            expected_spec_count,
            requires_sous_filiere,
        )

        level = data.get("level")
        filiere = data.get("filiere")
        sous_filiere = data.get("sous_filiere_techno")
        specialites = data.get("specialites", [])
        intended_track = data.get("intended_track")
        postbac_year = data.get("postbac_year")
        postbac_formation_type = data.get("postbac_formation_type")
        errors: dict[str, str] = {}

        if not level:
            errors["level"] = "Level is required for commit."

        if level == "college_3eme":
            if not intended_track:
                errors["intended_track"] = "intended_track is required for college_3eme."
            if filiere is not None:
                errors["filiere"] = "filiere must be null for college_3eme."
            if specialites:
                errors["specialites"] = "specialites must be empty for college_3eme."

        elif level in ("lycee_2nde", "lycee_1ere", "lycee_terminale"):
            if not filiere:
                errors["filiere"] = "filiere is required for lycee levels."
            if intended_track is not None:
                errors["intended_track"] = "intended_track must be null for lycee levels."

            if filiere and level:
                expected = expected_spec_count(level, filiere)
                if expected is not None:
                    # Validate specialite IDs belong to the right pool
                    if filiere == "general":
                        invalid = [s for s in specialites if s not in SPECIALITE_IDS]
                    else:  # pro
                        invalid = [s for s in specialites if s not in SPECIALITE_PRO_IDS]
                    if invalid:
                        errors["specialites"] = f"Invalid specialite IDs for {filiere}: {invalid}"
                    elif len(specialites) != expected:
                        errors["specialites"] = (
                            f"Expected {expected} specialite(s) for {level}/{filiere}, "
                            f"got {len(specialites)}."
                        )
                else:
                    # expected is None: techno or 2nde général/techno — no specialites allowed
                    if specialites:
                        errors["specialites"] = (
                            f"specialites must be empty for {level}/{filiere}."
                        )

                if requires_sous_filiere(level, filiere) and not sous_filiere:
                    errors["sous_filiere_techno"] = (
                        f"sous_filiere_techno is required for {level}/{filiere}."
                    )
                if not requires_sous_filiere(level, filiere) and sous_filiere:
                    errors["sous_filiere_techno"] = (
                        "sous_filiere_techno must be null for this level/filiere."
                    )

        elif level == "postbac":
            if not postbac_year:
                errors["postbac_year"] = "postbac_year is required for postbac."
            if not postbac_formation_type:
                errors["postbac_formation_type"] = (
                    "postbac_formation_type is required for postbac."
                )
            if filiere is not None:
                errors["filiere"] = "filiere must be null for postbac."
            if specialites:
                errors["specialites"] = "specialites must be empty for postbac."
            if intended_track is not None:
                errors["intended_track"] = "intended_track must be null for postbac."

        if errors:
            raise serializers.ValidationError(errors)
        return data

    def apply(self, level_profile: StudentLevelProfile) -> StudentLevelProfile:
        """Apply validated data to the model instance (does not save)."""
        data = self.validated_data

        if data.get("skip"):
            level_profile.mark_skipped()
            return level_profile

        for field in (
            "level",
            "filiere",
            "sous_filiere_techno",
            "intended_track",
            "postbac_year",
            "postbac_formation_type",
            "level_ref_version",
        ):
            if field in data:
                setattr(level_profile, field, data[field])

        if "specialites" in data:
            level_profile.specialites = data["specialites"]

        if data.get("commit"):
            # Normalize stale branch fields that are incompatible with the committed level.
            level = level_profile.level
            if level == "college_3eme":
                level_profile.filiere = None
                level_profile.sous_filiere_techno = None
                level_profile.specialites = []
                level_profile.postbac_year = None
                level_profile.postbac_formation_type = None
            elif level in ("lycee_2nde", "lycee_1ere", "lycee_terminale"):
                level_profile.intended_track = None
                level_profile.postbac_year = None
                level_profile.postbac_formation_type = None
            elif level == "postbac":
                level_profile.filiere = None
                level_profile.sous_filiere_techno = None
                level_profile.specialites = []
                level_profile.intended_track = None
            level_profile.mark_completed()
        elif level_profile.onboarding_step2_status == OnboardingStep2Status.PENDING:
            level_profile.onboarding_step2_status = OnboardingStep2Status.IN_PROGRESS

        return level_profile
