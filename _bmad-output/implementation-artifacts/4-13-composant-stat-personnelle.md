# Story 4.13: Composant `StatPersonnelle` (indicateur compatibilité additif)

**Epic:** 4 — Graphe de Parcours & Stats d'Admission (Deuxième Aha)
**Status:** ready-for-dev
**Sprint:** 7 (Graphe parcours)
**Story Key:** `4-13-composant-stat-personnelle`
**Estimation:** S

---

## 1. User Story

**As a** Path-Advisor developer
**I want** an optional, additive `StatPersonnelle` component that shows a 3-state compatibility indicator for students who have uploaded their bulletins
**So that** students with complete profiles get richer information without humiliating those who don't — the component simply disappears when unavailable (UX-DR20 + UX-DR25)

---

## 2. Acceptance Criteria (BDD)

### AC1 — Null state: component renders nothing

**Given** `StatPersonnelle` receives `compatibility={null}`
**When** it renders
**Then** the component returns `null` — no DOM node, no empty div, no placeholder
**And** no text "Ajoute tes bulletins pour voir ta compatibilité" or any call-to-action is displayed
**And** the layout of the parent (`FicheEcole`) is completely unaffected (no empty gap or reserved space)

### AC2 — State "compatible": green dot + label + tooltip

**Given** `compatibility="compatible"`
**When** the component renders
**Then** an 8px filled circle with color `bg-green-500` is displayed
**And** the text label "Profil compatible" is displayed in `text-sm text-green-700`
**And** a `<details>/<summary>` accessible tooltip is available: expanding it reveals the text `"Ton niveau correspond aux profils admis l'an dernier"`
**And** the `<summary>` element is the dot+label row itself (or a disclosure indicator next to it)

### AC3 — State "a_renforcer": orange dot + label + tooltip

**Given** `compatibility="a_renforcer"`
**When** the component renders
**Then** an 8px filled circle with color `bg-orange-400` is displayed
**And** the text label "À renforcer" is displayed in `text-sm text-orange-700`
**And** a `<details>/<summary>` accessible tooltip reveals: `"Quelques points de plus en [matière] t'aideraient"` (matière is passed via `tooltipDetail` prop or defaults to the generic string if not provided)

### AC4 — State "au_dessus": dark green dot + label + understated tooltip

**Given** `compatibility="au_dessus"`
**When** the component renders
**Then** an 8px filled circle with color `bg-green-700` is displayed
**And** the text label "Profil au-dessus" is displayed in `text-sm text-green-800`
**And** a `<details>/<summary>` tooltip reveals: `"Tu es au-dessus du niveau moyen admis"` (neutral framing — no "tu es trop bien pour eux")

### AC5 — UX-DR25: incomplete profile (Léa) — total absence

**Given** a student with `has_bulletins=False` (the Léa scenario)
**When** `FicheEcole` renders with `admissionStat.compatibility === null` (or `admissionStat.compatibility` is absent/undefined)
**Then** `StatPersonnelle` is not rendered at all
**And** no gap, no empty space, no "coming soon" indicator is left in the layout
**And** `FicheEcole` does NOT pass any "add your bulletins" message to `StatPersonnelle` — that responsibility belongs to a different onboarding flow

### AC6 — Positioned under `CarteAdmission` in `FicheEcole`

**Given** `FicheEcole` renders with `admissionStat.compatibility` present and non-null
**When** the school detail page renders
**Then** `StatPersonnelle` appears immediately below `CarteAdmission` in the DOM and visually
**And** a 4px gap (`mt-1` or `gap-1`) separates the two
**And** the visual hierarchy: `CarteAdmission` is primary, `StatPersonnelle` is secondary/additive

---

## 3. Tasks / Subtasks

### T1 — Backend: compute `compatibility` in `AdmissionPredictionService`

- [ ] Locate `AdmissionPredictionService` in `apps/api/apps/pathways/services/` (or `apps/api/apps/schools/services/` — check where Story 4.2's `predict_admission` service lives). Read the full service file before modifying.
- [ ] Add a `_compute_compatibility` private method:
  ```python
  def _compute_compatibility(
      self,
      student_profile,
      admission_stat,
  ) -> str | None:
      """
      Returns 'compatible', 'au_dessus', or 'a_renforcer'.
      Returns None if the student has no bulletin summary (has_bulletins=False).
      """
      if not student_profile.has_bulletins:
          return None

      bulletin_summary = getattr(student_profile, 'bulletin_summary', None)
      if bulletin_summary is None:
          return None

      moyenne_eleve = bulletin_summary.get('moyenne_generale')
      if moyenne_eleve is None:
          return None

      # admission_stat fields: moyenne_admis_min, moyenne_admis_max
      # These should already be stored in the admission_stats_history table (Story 4.2)
      moyenne_admis_min = admission_stat.get('moyenne_admis_min')
      moyenne_admis_max = admission_stat.get('moyenne_admis_max')

      if moyenne_admis_min is None:
          return None

      if moyenne_eleve >= (moyenne_admis_max or moyenne_admis_min) * 1.1:
          return 'au_dessus'
      elif moyenne_eleve >= moyenne_admis_min:
          return 'compatible'
      else:
          return 'a_renforcer'
  ```
- [ ] Call `_compute_compatibility` within the existing `predict_admission` method and include the result in the returned dict.
- [ ] If `moyenne_admis_min` and `moyenne_admis_max` are not yet present on the `admission_stats_history` or the related data structure, add them. These values should be derivable from the Parcoursup open data import (Story 4.2 already imports distribution data).

### T2 — Backend: expose `compatibility` in API response

- [ ] In `apps/api/apps/pathways/serializers.py` (or `schools/serializers.py` — wherever Story 4.2's prediction serializer lives), add `compatibility` as a read-only field:
  ```python
  class AdmissionPredictionResponseSerializer(serializers.Serializer):
      min_proba = serializers.FloatField()
      expected_proba = serializers.FloatField()
      max_proba = serializers.FloatField()
      label = serializers.ChoiceField(choices=["audacieux", "realiste", "sur", "estimation_indicative"])
      context_line = serializers.CharField()
      action_lever = serializers.CharField(allow_null=True)
      updated_at = serializers.DateTimeField(allow_null=True)
      compatibility = serializers.ChoiceField(
          choices=["compatible", "a_renforcer", "au_dessus"],
          allow_null=True
      )
  ```
- [ ] `compatibility=null` is a valid response (not an error). The serializer must NOT omit the field — always include it, even when null.
- [ ] Update `POST /api/v1/schools/predict-admission/` (Story 4.2 endpoint) to include `compatibility` in the response. Do not change any other field, endpoint path, or auth requirement.

### T3 — Frontend: `StatPersonnelle` component

- [ ] Create `apps/web/src/components/schools/StatPersonnelle.tsx`:
  ```typescript
  interface StatPersonnelleProps {
    compatibility: "compatible" | "a_renforcer" | "au_dessus" | null | undefined
    school: { name: string }      // for tooltip context if needed
    tooltipDetail?: string        // optional override for the 'a_renforcer' tooltip text
    className?: string
  }
  ```
- [ ] Early return guard:
  ```typescript
  if (!compatibility) return null
  ```
- [ ] Config map (avoids long conditionals):
  ```typescript
  const CONFIG = {
    compatible: {
      dotClass: "bg-green-500",
      label: "Profil compatible",
      labelClass: "text-green-700",
      tooltip: "Ton niveau correspond aux profils admis l'an dernier",
    },
    a_renforcer: {
      dotClass: "bg-orange-400",
      label: "À renforcer",
      labelClass: "text-orange-700",
      tooltip: null, // filled from tooltipDetail prop or fallback
    },
    au_dessus: {
      dotClass: "bg-green-700",
      label: "Profil au-dessus",
      labelClass: "text-green-800",
      tooltip: "Tu es au-dessus du niveau moyen admis",
    },
  } as const
  ```
- [ ] Render:
  ```jsx
  const config = CONFIG[compatibility]
  const tooltipText = compatibility === "a_renforcer"
    ? (tooltipDetail ?? "Quelques points de plus en mathématiques t'aideraient")
    : config.tooltip

  return (
    <details className={cn("group text-sm", className)}>
      <summary className="flex items-center gap-1.5 cursor-pointer list-none">
        <span
          className={cn("inline-block w-2 h-2 rounded-full flex-shrink-0", config.dotClass)}
          aria-hidden="true"
        />
        <span className={config.labelClass}>{config.label}</span>
        <span className="text-slate-400 text-xs group-open:hidden" aria-hidden="true">ⓘ</span>
      </summary>
      {tooltipText && (
        <p className="mt-1 pl-3.5 text-xs text-slate-500">{tooltipText}</p>
      )}
    </details>
  )
  ```
- [ ] Note: `<details>/<summary>` provides keyboard and screen-reader accessible disclosure without JavaScript. The `<summary>` is natively focusable and activatable via Enter/Space. No `useState` needed for the tooltip open/closed state.

### T4 — Frontend: integrate `StatPersonnelle` in `FicheEcole`

- [ ] In `apps/web/src/components/schools/FicheEcole.tsx` (Story 4.10), locate the admission stat block where `<CarteAdmission>` was placed (by Story 4.11).
- [ ] Add `StatPersonnelle` immediately after `CarteAdmission`:
  ```jsx
  <div className="flex flex-col gap-1">
    <CarteAdmission
      admissionStat={admissionStat}
      variant={variant === "expanded" ? "medium" : "small"}
      schoolName={school.name}
      schoolSlug={school.slug}
    />
    <StatPersonnelle
      compatibility={admissionStat?.compatibility ?? null}
      school={school}
    />
  </div>
  ```
- [ ] If `admissionStat` is `null` or `undefined` (data still loading), `StatPersonnelle` receives `null` and renders nothing — no guard needed beyond the early return inside `StatPersonnelle`.
- [ ] Do NOT add any conditional "Add bulletins" UI around `StatPersonnelle`. The component's null return handles this silently.

### T5 — Tests

**`apps/web/src/components/schools/__tests__/StatPersonnelle.test.tsx`**:

- [ ] `compatibility={null}` → `render` returns empty container (use `container.firstChild` to assert null or `queryByText` finds nothing)
- [ ] `compatibility={undefined}` → same as null (defensive check)
- [ ] `compatibility="compatible"` → text "Profil compatible" is visible; dot has class `bg-green-500`; `<details>` is present; expanding it (fire click on `<summary>`) reveals tooltip text "Ton niveau correspond aux profils admis l'an dernier"
- [ ] `compatibility="a_renforcer"` → text "À renforcer" visible; dot `bg-orange-400`; default tooltip text visible when expanded
- [ ] `compatibility="a_renforcer"` with `tooltipDetail="Renforce tes maths"` → expanded tooltip shows "Renforce tes maths" (not the default)
- [ ] `compatibility="au_dessus"` → text "Profil au-dessus"; dot `bg-green-700`; tooltip text does NOT contain "trop bien pour eux"
- [ ] In all non-null cases: no text matching /ajoute.*bulletins/i is present in the rendered output
- [ ] `<summary>` element is present and has no `aria-hidden` (it must be focusable)

**`apps/api/apps/pathways/tests/test_services.py`** (or equivalent for Story 4.2 service):

- [ ] `_compute_compatibility` with `has_bulletins=False` → returns `None`
- [ ] `_compute_compatibility` with `moyenne_eleve=15.0`, `moyenne_admis_min=13.0`, `moyenne_admis_max=16.0` → `"compatible"`
- [ ] `_compute_compatibility` with `moyenne_eleve=17.8`, `moyenne_admis_min=13.0`, `moyenne_admis_max=16.0` → `"au_dessus"` (17.8 ≥ 16.0 × 1.1 = 17.6)
- [ ] `_compute_compatibility` with `moyenne_eleve=11.0`, `moyenne_admis_min=13.0` → `"a_renforcer"`
- [ ] `_compute_compatibility` with `moyenne_admis_min=None` → returns `None` (no crash)

---

## 4. Dev Notes

### The core UX invariant (UX-DR25)

**Mode normal = mode dégradé.** There must be zero visual difference between a student with bulletins and one without — other than `StatPersonnelle` being present or absent. The absence of `StatPersonnelle` must be seamless: no empty box, no skeleton, no message. This is enforced by the `if (!compatibility) return null` guard inside the component — the parent component (`FicheEcole`) unconditionally renders `<StatPersonnelle compatibility={...} />` without any surrounding conditional wrapper.

### Why `<details>/<summary>` instead of hover tooltip

The project targets mobile-first with RGAA AA compliance. Hover-only tooltips fail on touch devices and assistive technologies. `<details>/<summary>` is:
1. Natively keyboard accessible (Tab + Enter/Space)
2. Screen-reader compatible out of the box
3. No JavaScript state required
4. Touch-compatible (tap to expand)

### Backend location investigation required

The story assumes Story 4.2's `AdmissionPredictionService` lives in `apps/api/apps/pathways/services/`. However, given the `apps/api/apps/professions/` directory was spotted in git status as untracked, the pathways/schools app structure may differ. **Before writing any backend code**, run:
```bash
find apps/api/apps -name "services.py" -o -name "services" -type d | head -10
grep -r "predict_admission\|AdmissionPrediction" apps/api/apps/ --include="*.py" -l
```
Then read the actual service file before modifying.

### `AdmissionStat` type extension

Story 4.11 added `compatibility` as an optional field to the `AdmissionStat` TypeScript interface:
```typescript
compatibility?: "compatible" | "a_renforcer" | "au_dessus" | null
```
This story does NOT need to re-add it — it was already declared in Story 4.11's T1. Verify the field is present in `apps/web/src/lib/api/schools.ts` (or `types/schools.ts`) before proceeding with T3.

### Inverted logic: "au_dessus" threshold

The `au_dessus` computation uses `moyenne_admis_max * 1.1` (10% above the maximum admitted average). This is intentional: a student exactly at the max admitted average is still "compatible" (not yet "au_dessus"). The 10% buffer avoids the edge case where minor grade fluctuations flip the state.

### Reference files

- `apps/api/apps/pathways/services/` or `apps/api/apps/schools/services/` — Story 4.2 service (investigate location)
- `apps/web/src/components/schools/FicheEcole.tsx` — integration target (T4)
- `apps/web/src/components/schools/CarteAdmission.tsx` (Story 4.11) — rendered directly above `StatPersonnelle`
- `apps/web/src/lib/api/schools.ts` or `types/schools.ts` — `AdmissionStat` type (verify `compatibility` field is present from Story 4.11)

---

## 5. Dev Agent Record

### Agent Model Used
_À remplir_

### Completion Notes List
_À remplir_

### File List
_À remplir_

### Change Log
- 2026-06-21 — Story 4.13 créée.
