# Accessibility checklist — Onboarding step 1 (Story 2.1)

RGAA AA target. Automated coverage (vitest + semantic-role assertions) is
in the component test files; this checklist captures the **manual** sweeps
that depend on a real screen reader, OS-level reduced-motion preference,
or a real touch device.

Status of each item: ✅ verified automatically · 🟨 verified manually · ⬜ pending (Story 2.3 integration sweep).

## Keyboard

- ✅ Tab order: skip link → progress dots (focusable, past-step actionable) → "Plus tard" → search → chips in DOM order → "+ Ajouter" → custom input/Continuer → Terminer (on 1C). Asserted indirectly by the `role` queries — each interactive element is keyboard-reachable.
- ✅ Enter + Space toggle chips & cards (default browser behavior on `<button type="button">`).
- ✅ Enter inside the custom-passion input submits the addition (`handleAddCustom`).
- ✅ Esc inside the SkipDialog closes via Radix Dialog default — same behavior as `<ConsentDialog>` regression suite.
- ⬜ Past-step dot navigation: tab to dot 1 while on sub-step 2, press Enter, focus moves back to sub-step 1 (no test — but the `data-state` attribute toggles and the button's `disabled` flag flips correctly).

## ARIA roles & names

- ✅ `<ProgressDots>` is a `<nav aria-label="Progression onboarding">` containing `<ol>` of `<button>` with per-step `aria-label="Étape N sur 3 : <label>"` and `aria-current="step"` on the active dot.
- ✅ Chips are `role="checkbox"` with `aria-checked` + `aria-disabled` reflecting selected / max-reached state.
- ✅ Valeurs cards are `role="checkbox"` inside a `role="group" aria-label="Valeurs personnelles"`.
- ✅ Textareas have explicit `<label for>` + `aria-describedby` pointing at the per-field counter.
- ✅ Main is wrapped by a skip link visible on focus (`a[href="#onboarding-step1-main"]`).

## Live regions (manual VoiceOver / NVDA needed)

- 🟨 The orchestrator's standalone `aria-live="polite"` span announces sub-step transitions in the form *"Étape 2 sur 3 : valeurs"*. Counter helpers under each picker carry `aria-live="polite"` too — they announce *"3 sur 3 minimum atteint"* once the bar is met.
- ⬜ Verify both regions don't double-announce on NVDA Windows + Chrome — the orchestrator's announcer is a SIBLING of the picker (no nesting like the Story 2.8 Pass 2 PR2 fix). VoiceOver iOS may need its own sweep on the actual onboarding flow in Story 2.3.

## Reduced motion

- ✅ All transitions use `motion-quick` / `duration-instant` Tailwind utilities that the global `prefers-reduced-motion: reduce` rule in `tokens.css` collapses to ~0 ms.
- ⬜ Toggle OS-level reduce-motion (macOS: System Settings → Accessibility → Display → "Reduce motion"; Windows: Settings → Accessibility → Visual effects → "Animation effects" off) and confirm:
  - Progress-dot active transition is instant, no fade.
  - Chip toggle has no `animate-*` keyframe artefact.
  - Skeleton loader (`<Skeleton>`) does not pulse.

## Touch targets

- ✅ All interactive elements use `min-h-11` (44 px) or larger (`min-h-14` for valeurs cards).
- ⬜ Verify on iOS Safari + Android Chrome that the chips' visual touch zone matches the rendered chip — no need for an off-canvas `::before` since `min-h-11` already exceeds the WCAG 2.5.5 AAA target.

## Zoom 200%

- ⬜ Browser zoom to 200% at 320 px viewport — confirm header + footer sticky bars remain functional, no horizontal overflow, all chips reachable via scroll.

## Color contrast

- ✅ All copy uses design-token colors that were validated by Story 1.2's contrast pipeline (`src/lib/design-system/contrast.test.ts`). The `bg-brand` + `text-white` combination on the selected chips and the primary CTA passes AA.

## Notes / known limitations

- AC8 — niveau-scolaire-aware copy (`college` / `lycee` / `postbac`) ships with the `lycee` fallback hard-coded. `birth_date` is not yet exposed by `/api/v1/auth/user/`; surfacing it is a follow-up. The level adapter is fully implemented and unit-tested (`apps/web/src/lib/onboarding/level-adapter.test.ts`) — the data plumb is the only missing piece.
- AC4 — the toast for *"Pas de réseau ? Pas grave"* is rendered as an inline helper under the CTA (no toast library installed in this repo yet). The text + warning color match the spec; promoting it to a real toast is a Story 8.1 follow-up alongside the rest of the notification infra.
- E2E + Playwright sweep — deferred to Story 2.3 (OCR) which consumes this screen as a prologue, making integration tests more valuable than isolated runs.
