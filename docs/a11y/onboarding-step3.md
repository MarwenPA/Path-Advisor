# Accessibility — Onboarding Step 3 (Bulletins OCR)

RGAA AA compliance notes for Story 2.3.

## 3-Card Choice

- Each card is a `<button>` with a descriptive `aria-label` (icon + text label)
- No visual hierarchy between cards (all same size, weight, colour) — AC1 requirement
- Focus ring visible, keyboard-navigable left/right

## File Picker Sheet

- Sheet uses `role="dialog"` with `aria-modal="true"` and `aria-labelledby`
- Focus trapped inside sheet while open
- File list items: `<li>` with filename + size, error message in `role="alert"` when validation fails
- Remove button: `aria-label="Supprimer {filename}"`
- Min touch target 44×44 px on all interactive elements

## Upload Progress

- Each progress bar: `<progress>` or `role="progressbar"` with `aria-valuenow`, `aria-valuemin=0`, `aria-valuemax=100`, `aria-label="{filename} — upload"`
- Status container: `aria-live="polite"` for non-urgent updates
- "Completed" state announced via `aria-live` region

## OCR Loader

- Wraps `<ScenarioLoader>` which handles its own `role="status"` and `aria-live="polite"`
- Manual fallback link: keyboard-reachable, not hidden from AT

## Recap Editor (BulletinRecapEditor)

- Semantic `<table>` with `<thead>` / `<tbody>` / `<th scope="col">`
- Editable note cells: `<input type="number" min="0" max="20">` with `aria-label="Note — {matière}"`
- Low-confidence indicator: `data-low-confidence` + `aria-label="Confiance faible — vérifier"` on the warning icon (Tooltip text also visible on hover/focus)
- Multi-bulletin tabs: `role="tablist"`, each tab `role="tab"`, panel `role="tabpanel"` with `aria-labelledby`
- Validate button: descriptive `aria-label` ("Valider le bulletin {label}")

## Graceful Fallback

- Two CTAs with equal visual weight (no primary/secondary styling difference) — AC7 requirement
- Both are `<button>` elements (not anchors) since they trigger in-page state changes
- No "recommended" label on either option

## Reduced Motion

All animated transitions respect `prefers-reduced-motion: reduce`:
- OCR loader animation paused or replaced with a static "Analyse en cours…"
- Upload progress bar transitions set to `0ms` duration
- Sheet enter/exit animations skipped

## Colour Contrast

- Text on cards: meets 4.5:1 minimum
- Low-confidence warning icon: amber, meets 3:1 against white background (graphical element threshold)
- Progress bar fill: brand colour, checked at 3:1 against track background
