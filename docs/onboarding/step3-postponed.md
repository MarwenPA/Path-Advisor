# Step 3 — Mode dégradé invisible ("Plus tard" bulletins)

Story 2.5 — Experience Principle #4: *The normal mode contains all modes.*

## Flow

```
3rd card "Plus tard" → POST /api/v1/students/me/bulletins/postpone
  → bulletins_status = "postponed"
  → redirect /dashboard (silent, no toast)
```

Dashboard and all product pages show the **identical UI** as users with bulletins.
The only differences are in **label copy** — never in structure, layout, or visual affordances.

## Cross-cut contracts

### Epic 3 — ScoreVocationnel (Story 3.11)

When `bulletins_status === "postponed"`, the `ScoreVocationnel` component must:
- Keep the same visual structure and score chip
- Omit the "Signaux scolaires" section entirely (do NOT render an empty placeholder)
- Append to the recopiable phrase: *"— précision affinée quand tu ajouteras tes bulletins."*

### Epic 4 — CarteAdmission (Story 4.5) + GraphParcours (Story 4.9)

When `bulletins_status === "postponed"`:
- Display admission stats as a wide range (e.g. `30-45 %`) instead of a single figure
- Label: *"Pari audacieux — estimation indicative"*
- Replace the "lever" line with: *"Affine cette estimation avec tes bulletins."*
- Render `<BulletinsMiniCTA context="graph" />` below the school grid

### Epic 6 — StoryExport

Re-rendered PNG/PDF must include a subtle footnote: *"Estimation indicative — stats personnalisées après ajout des bulletins."*

## Anti-patterns (forbidden)

- ❌ "Profil incomplet" anywhere for a postponed user
- ❌ Empty sections with placeholder "Connecte tes bulletins pour voir"
- ❌ Visual or structural difference from users with bulletins
- ❌ "Débloque tes vraies stats"
- ❌ Percentage bars or completion gauges
