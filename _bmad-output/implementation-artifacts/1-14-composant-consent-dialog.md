# Story 1.14: Reusable `ConsentDialog` Component

**Epic:** 1 — Foundation: Multi-role Auth, RBAC, GDPR Compliance & Technical Infrastructure
**Status:** done
**Sprint:** 1 (Foundations)
**Story Key:** `1-14-composant-consent-dialog`
**Estimation:** S–M (small to medium) — pure front-end, no backend changes, no DB migration. Composes shadcn primitives already shipped by Story 1.2 (`Dialog`, `Button`). Sized small (~3–4 h focused work) but structurally critical: this is the **first Couche 3 Path-Advisor custom component** in the codebase and it sets the convention for every composite that follows (`ScoreVocationnel`, `FicheMetier`, `GraphParcours`, …).

> Story 1.14 turns the abstract "granular consent" UX pattern (UX-DR11 + UX-DR26) into a concrete, reusable React component. It is parallel-safe with Stories 1.3 / 1.4 (no shared files), and unblocks 1.4 (parental opt-in modal), 1.10 (revocation), 1.12 (account deletion), 5.3 (paywall confirm), 6.7 (counselor profile-view consent).

---

## 1. User Story

**As a** Path-Advisor developer (Marwen, solo team),
**I want** a standardised `<ConsentDialog />` component covering the three critical MVP consent cases (parental < 15, counselor, partner school) with title / description / data mentioned / duration / beneficiary props and accept/refuse callbacks of equal visual weight,
**So that** every multi-role consent flow in the product (Stories 1.4, 1.10, 1.12, 5.3, 6.7) reuses the same RGPD-compliant, non-dark-pattern, screen-reader-correct dialog without each consumer re-inventing layout, focus management, or audit metadata.

**Business value:** the component is a **regulatory primitive** — Path-Advisor handles minors' data; every consent capture must be auditable (FR12), revocable (FR9), non-culpabilising (UX principle), and identical regardless of which feature triggers it. Without a shared component, each consumer would drift on copy, button weighting, or accessibility, and the product would fail RGAA AA audit. UX risk flagged: "ConsentDialog trop complexe pour un solo founder — démarrer avec les 3 cas critiques (parental < 15 ans, conseillère, école) puis étendre" (UX spec §Risques composants). This story respects that scoping.

---

## 2. Acceptance Criteria (BDD)

### AC1 — Component API: props contract

**Given** I import `ConsentDialog` from `@/components/ui/consent-dialog`
**When** I read its TypeScript signature
**Then** the props are exactly:

```ts
export type ConsentMeta = {
  /** ISO 8601 UTC timestamp at the moment the user clicked Accept. */
  acceptedAt: string;
  /** SHA-256 hex digest of a deterministic JSON of the dialog content
   *  (title + description + dataMentioned + duration + beneficiary). Used as
   *  immutability proof in the audit log (FR12). */
  contentHash: string;
};

export type ConsentDialogProps = {
  /** Controlled visibility. */
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** Concrete consent context (caller passes localized French strings). */
  title: string;
  description: string;
  dataMentioned: string[];
  duration: string;
  beneficiary: string;
  /** CTA labels. Defaults: "Accepter" / "Refuser". */
  acceptLabel?: string;
  refuseLabel?: string;
  /** When true, the accept action is styled as destructive (revocation, deletion). */
  isAcceptDestructive?: boolean;
  /** Disables both CTAs and shows an inline spinner on accept while async work runs. */
  isSubmitting?: boolean;
  /** Required: called with the freshly-computed ConsentMeta. May be async. */
  onAccept: (meta: ConsentMeta) => void | Promise<void>;
  /** Optional: defaults to closing the dialog. */
  onRefuse?: () => void;
};
```

**And** `ConsentMeta` is exported as a named export usable by callers writing audit-log payloads.
**And** the component is the **default export** of `consent-dialog.tsx` and is also a **named export** `ConsentDialog`.

### AC2 — Responsive layout: modal desktop / bottom-sheet mobile

**Given** the UX spec § Responsive Behavior states: ConsentDialog = Sheet bottom (mobile), Sheet bottom 75 % (tablet), Modal centered (desktop)
**When** I open the dialog on a viewport
**Then**

- **< 640 px (mobile, Tailwind `sm` breakpoint)** — content renders as a **bottom sheet**: pinned to the bottom edge (`fixed bottom-0 left-0 right-0`), full viewport width, rounded top corners only (`rounded-t-lg rounded-b-none`), no left/right margin, max-height 90 vh, internal scroll if content exceeds.
- **≥ 640 px (tablet + desktop)** — content renders as a **centered modal**: standard shadcn `DialogContent` positioning (`sm:left-1/2 sm:top-1/2 sm:-translate-x-1/2 sm:-translate-y-1/2`), `max-width: 32rem` (`sm:max-w-lg`), full rounding (`sm:rounded-lg`).

**And** the open/close animation uses `motion-quick` (200 ms) for the content and `motion-quick` for the overlay opacity. **No `motion-narrative`** — that token is reserved for Epic 4 graph (Story 1.2 §Motion contract).
**And** `prefers-reduced-motion: reduce` collapses transitions to ~0 ms via the global rule shipped in `tokens.css`.

### AC3 — No-dark-pattern button visual contract

**Given** the UX spec § Button Hierarchy and the FR mandate "boutons même poids visuel"
**When** I render the dialog with the default refuse / accept pair
**Then** both buttons share the **same size class** (`size="default"`), the **same height** (40 px), the **same horizontal padding** (px-4), the **same font weight** (`font-medium` from buttonVariants), and **the same DOM order on screen reader** (refuse first → accept second in source DOM order; visual order may invert at `sm:` to put accept on the right).

**And** the default pair uses `variant="outline"` for refuse and `variant="default"` (brand) for accept — both fully styled, neither greyed/de-emphasised.
**And** when `isAcceptDestructive=true`, the accept button uses `variant="destructive"` (danger red, `#9E2A24`) and the refuse button keeps `variant="outline"` — still equal visual weight, only intent colour changes.
**And** a Vitest test asserts both buttons share the *exact same* `className` substring for size: `h-10 px-4 py-2`.

### AC4 — Accessibility: role dialog, focus trap, ESC, labels

**Given** the component composes Radix `@radix-ui/react-dialog`
**When** the dialog is open
**Then** it has `role="dialog"` and `aria-modal="true"` (Radix default).
**And** the dialog has an accessible name pointing to the title via `aria-labelledby` (DialogTitle id).
**And** the description is wired via `aria-describedby` to the DialogDescription id.
**And** **focus is trapped** within the dialog (Radix-managed); pressing `Tab` from the last focusable cycles to the first.
**And** pressing **ESC** closes the dialog and calls `onOpenChange(false)` and `onRefuse()` (treating ESC as a refusal, per UX-DR26 "ESC ferme").
**And** initial focus lands on the **refuse button** (safer default — pressing Enter on a focused accept would be a dark pattern), implemented via `<Button autoFocus>` on refuse or via `onOpenAutoFocus` event.
**And** the close `X` icon at top-right (inherited from shadcn `Dialog`) **is hidden** in `ConsentDialog` (`<DialogContent>` consumes only the structural primitives, not the auto-injected close button) — closure must be an explicit Accept or Refuse, not an ambiguous "X" that some users interpret as "save and close".
**And** the brand 2 px `:focus-visible` ring (Story 1.2 globals) is visible on Tab.
**And** a `lang="fr"` is inherited from `<html>` (Story 1.1).

### AC5 — Content hash (immutability proof for audit)

**Given** the `ConsentMeta.contentHash` must be a deterministic SHA-256 of the dialog content
**When** the user clicks Accept
**Then** the hash is computed using **`window.crypto.subtle.digest("SHA-256", ...)`** (Web Crypto API, no external dependency).
**And** the input to the hash is the **UTF-8 bytes of a deterministic JSON** with **sorted keys**, structure exactly (8 fields — extended from the original 5 during code-review decision D1 to ensure visually-different consents always produce different hashes for audit forensics):

```json
{
  "acceptLabel": "...",
  "beneficiary": "...",
  "dataMentioned": ["..."],
  "description": "...",
  "duration": "...",
  "isAcceptDestructive": false,
  "refuseLabel": "...",
  "title": "..."
}
```

`dataMentioned` is preserved in caller-supplied order (it represents a deliberate list, not a set). All other keys are alphabetically sorted at the top level. `acceptLabel` and `refuseLabel` reflect the **resolved** labels — i.e., if the caller passes `acceptLabel=""` or omits it, the hash uses the French default `"Accepter"` because that is what the user actually saw. `JSON.stringify` with an explicit sorted-keys replacer guarantees byte-stability across browsers.

**And** the hash is a **lowercase 64-character hex string** (SHA-256 = 32 bytes = 64 hex chars).
**And** `acceptedAt` is captured **immediately before** the hash computation, formatted via `new Date().toISOString()` (UTC).
**And** Vitest tests assert: (a) given identical props, the same hash is produced across 10 successive calls (determinism); (b) changing `title` produces a different hash (sensitivity); (c) flipping `isAcceptDestructive` produces a different hash (intent-sensitivity); (d) changing `acceptLabel` produces a different hash (label-sensitivity).

### AC6 — Three MVP critical cases rendered & smoke-tested

**Given** the UX spec calls out the three MVP cases: **parental < 15 ans**, **conseillère**, **école partenaire**
**When** I add a new section "Consent dialog" to `/design-system` (extending the showcase page shipped by the user during Story 1.2)
**Then** the section renders **three live triggers**, each opening a `ConsentDialog` with realistic French strings:

| Case | Title | Beneficiary | Data mentioned | Duration |
|---|---|---|---|---|
| **Parental < 15** | "Autorisation d'inscription de votre enfant" | "Mehdi, 14 ans" | "Profil scolaire, métiers explorés, parcours sauvegardés" | "Tant que l'inscription est active ; révocable à tout moment" |
| **Counselor** | "Donner accès à votre conseillère d'orientation" | "Mme Dupont, Lycée Henri-IV" | "Métiers recommandés, parcours sauvegardés, échéances Parcoursup (PAS les bulletins ni les motivations libres)" | "12 mois ; révocable à tout moment" |
| **Partner school** | "Envoyer votre profil à HEC Paris" | "HEC Paris (école partenaire)" | "Nom, prénom, profil scolaire, motivation libre, parcours visé" | "Une seule consultation ; révocation possible mais l'école conserve ses réponses émises" |

**And** the showcase entries demonstrate the three intent variants:

1. **Parental** → default brand accept (intent: opt-in)
2. **Counselor** → default brand accept (intent: opt-in)
3. **Account deletion** (fourth case, illustrating `isAcceptDestructive=true`) → destructive accept (intent: dangerous opt-in)

> Note: school partner = opt-in (not destructive) — keep brand accept. The destructive variant case slot is filled by "Supprimer mon compte" (preview of Story 1.12) to demonstrate the prop.

**And** each trigger button (in `/design-system`) is labelled clearly enough that the smoke test described in §Manual validation can be done without reading code.

### AC7 — Automated tests cover happy path + accessibility contracts

**Given** the story is implemented
**When** I run `npm test` in `apps/web`
**Then** at least the following **Vitest** tests pass under `apps/web/src/components/ui/consent-dialog.test.tsx`:

1. `renders title, description, data mentioned list, duration, and beneficiary verbatim`
2. `defaults to "Accepter" / "Refuser" labels when acceptLabel / refuseLabel are not provided`
3. `clicking accept calls onAccept with a ConsentMeta whose acceptedAt is a valid ISO 8601 UTC and contentHash is 64 lowercase hex chars`
4. `clicking refuse calls onRefuse and triggers onOpenChange(false)`
5. `ESC key triggers onRefuse and onOpenChange(false)` *(test via `userEvent.keyboard("{Escape}")`)*
6. `both accept and refuse buttons carry the same shadcn size class (h-10 px-4 py-2)` — enforced via `className.includes(...)` assertions
7. `isAcceptDestructive=true renders the accept button with bg-destructive class`
8. `isSubmitting=true disables both buttons and renders an inline spinner inside the accept button`
9. `contentHash is deterministic — same props produce identical hashes over 10 invocations` (tests AC5 stability)
10. `the dialog has aria-labelledby pointing to the title element and aria-describedby pointing to the description element`

**And** the test file uses `@testing-library/react` + `@testing-library/user-event` (Story 1.1 stack, already in deps).
**And** **no `@testing-library/dom` deprecation warnings** appear (the existing setup is clean).
**And** the existing test count in `apps/web` rises from `8` (Stories 1.1 + 1.2) to `≥ 18` after this story merges.

---

## 3. Tasks / Subtasks

### T1 — Component scaffolding (AC1, AC2, AC3)

- [ ] T1.1 Create file `apps/web/src/components/ui/consent-dialog.tsx` with `"use client"` directive at top.
- [ ] T1.2 Import shadcn primitives **already shipped by Story 1.2**: `Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle` from `@/components/ui/dialog`, `Button` from `@/components/ui/button`, `cn` from `@/lib/utils`.
- [ ] T1.3 Implement and export `ConsentMeta` and `ConsentDialogProps` types per AC1.
- [ ] T1.4 Implement the `ConsentDialog` functional component:
  - Render `<Dialog open={open} onOpenChange={...}>` wrapping a `<DialogContent>` with the **responsive className** documented in AC2:
    ```tsx
    <DialogContent
      className={cn(
        // Mobile bottom-sheet (< 640 px)
        "fixed bottom-0 left-0 right-0 top-auto translate-x-0 translate-y-0 max-h-[90vh] w-full max-w-none overflow-y-auto rounded-t-lg rounded-b-none",
        // Tablet + desktop modal (≥ 640 px) — restore shadcn defaults
        "sm:left-1/2 sm:top-1/2 sm:bottom-auto sm:right-auto sm:-translate-x-1/2 sm:-translate-y-1/2 sm:max-w-lg sm:rounded-lg",
        // Equalise animation timing to motion-quick (token from Story 1.2)
        "duration-quick",
      )}
      // Hide the auto-injected X close button by overriding its parent.
      // Radix-managed Close is inherited from DialogContent; we suppress it
      // by passing a custom child below and not adding an explicit X trigger.
    >
    ```
  - **Important — close the auto X**: the shipped `DialogContent` (Story 1.2) embeds a `DialogPrimitive.Close` X button. ConsentDialog must **not** show this X (AC4). Solution: copy the structural composition of `DialogContent` locally — render `DialogPortal > DialogOverlay > DialogPrimitive.Content` directly inside `consent-dialog.tsx` without the inner `<X>` button. This avoids modifying the shared `Dialog` primitive. See §4.5 below for the exact JSX.
- [ ] T1.5 Inside the content, render in this DOM order:
  1. `<DialogHeader>` with `<DialogTitle>{title}</DialogTitle>` and `<DialogDescription>{description}</DialogDescription>`.
  2. A `<section>` listing structural metadata:
     - "Données concernées" → `<ul>` of `dataMentioned`
     - "Durée" → `<p>` of `duration`
     - "Bénéficiaire" → `<p>` of `beneficiary`
     - Each pair styled `text-body-sm text-text-muted` for labels and `text-body text-text` for values (tokens from Story 1.2).
  3. A `<DialogFooter>` with the two `<Button>` instances in **source order refuse → accept** (per AC4):
     - Refuse: `<Button variant="outline" autoFocus disabled={isSubmitting}>{refuseLabel ?? "Refuser"}</Button>`
     - Accept: `<Button variant={isAcceptDestructive ? "destructive" : "default"} disabled={isSubmitting}>{acceptLabel ?? "Accepter"}</Button>` — if `isSubmitting`, render `<Loader2 className="mr-2 h-4 w-4 animate-spin" />` (Lucide icon, already in deps as `lucide-react`).
- [ ] T1.6 Use `onOpenAutoFocus` on `DialogPrimitive.Content` to call `event.preventDefault()` then `refuseButtonRef.current?.focus()` — guarantees focus lands on Refuse, not Accept (AC4).
- [ ] T1.7 Export `ConsentDialog` as both **named and default** export.

### T2 — Content hash + accept handler (AC5)

- [ ] T2.1 Implement a private helper `computeContentHash(props): Promise<string>` inside the file:
  ```ts
  async function computeContentHash(input: {
    title: string;
    description: string;
    dataMentioned: string[];
    duration: string;
    beneficiary: string;
  }): Promise<string> {
    const canonical = JSON.stringify({
      beneficiary: input.beneficiary,
      dataMentioned: input.dataMentioned, // preserve caller order
      description: input.description,
      duration: input.duration,
      title: input.title,
    });
    const bytes = new TextEncoder().encode(canonical);
    const digest = await window.crypto.subtle.digest("SHA-256", bytes);
    return Array.from(new Uint8Array(digest))
      .map((b) => b.toString(16).padStart(2, "0"))
      .join("");
  }
  ```
- [ ] T2.2 Wire the accept button click handler:
  ```ts
  const handleAccept = async () => {
    const acceptedAt = new Date().toISOString();
    const contentHash = await computeContentHash({ title, description, dataMentioned, duration, beneficiary });
    await onAccept({ acceptedAt, contentHash });
  };
  ```
  **Important:** capture `acceptedAt` **before** awaiting the hash (the spec says "at the moment the user clicked Accept"). Computing the hash is < 1 ms but conceptually it must reflect click time.
- [ ] T2.3 Wire the refuse button + ESC close path:
  ```ts
  const handleRefuse = () => {
    onRefuse?.();
    onOpenChange(false);
  };
  ```
  And ensure the `Dialog`'s `onOpenChange` propagates ESC to `handleRefuse` — Radix calls `onOpenChange(false)` on ESC; intercept it:
  ```ts
  const handleOpenChange = (next: boolean) => {
    if (!next) onRefuse?.();
    onOpenChange(next);
  };
  ```

### T3 — Vitest unit tests (AC7)

- [ ] T3.1 Create `apps/web/src/components/ui/consent-dialog.test.tsx`.
- [ ] T3.2 Implement the **10 tests** listed in AC7 using `@testing-library/react` (already in deps — Story 1.1 stack). **Do NOT add `@testing-library/user-event`** (not currently in deps and unnecessary for this scope; `fireEvent` is sufficient).
- [ ] T3.3 For the hash determinism test (AC7 #9), call `computeContentHash` indirectly: render the dialog, click accept, capture the resolved `contentHash`, repeat 10× with the same props, assert all 10 values are equal. (The Web Crypto API is available in the JSDOM env shipped by `vitest` ≥ v2 + Node 20+ — confirmed in Story 1.1 stack.)
- [ ] T3.4 For the ESC test (AC7 #5), use `fireEvent.keyDown(document.body, { key: "Escape" })` after opening the dialog. Radix Dialog listens on the document and propagates to the `onOpenChange` handler.
- [ ] T3.5 For the same-size-class test (AC7 #6), query both buttons by role and assert `className.includes("h-10 px-4 py-2")` on each.
- [ ] T3.6 For async hash assertions, wrap the accept click in `await act(async () => { ... })` then `await waitFor(() => expect(onAccept).toHaveBeenCalled())` — `subtle.digest` returns a Promise.

### T4 — Extend `/design-system` showcase (AC6)

- [ ] T4.1 Open `apps/web/src/app/design-system/page.tsx` (created by the user during Story 1.2 — read it before editing to preserve existing sections).
- [ ] T4.2 Add a new `<section aria-labelledby="consent-dialog-heading">` after the existing "Components" section.
- [ ] T4.3 In a sub-file `apps/web/src/app/design-system/_components/consent-dialog-demos.tsx` (Client Component, `"use client"`) — keep the page itself a Server Component — implement four `<Button>` triggers, each with its own `useState<boolean>(false)` + matching `<ConsentDialog>`, covering the four cases from AC6 (parental / counselor / partner school / account deletion).
- [ ] T4.4 In each demo's `onAccept` callback, simply `console.info("[consent] accepted", meta)` for visual smoke-testing. The audit log call site is **not in scope of this story** (deferred to Story 1.13 + each consuming feature story).
- [ ] T4.5 In the new section header, add a one-paragraph explanation: "ConsentDialog: composite Couche 3 component. Three MVP cases shown live. Hover/focus/keyboard the triggers — both buttons must feel equally weighted (no dark pattern)."

### T5 — Manual validation checklist (a11y, screen-reader, mobile)

- [ ] T5.1 Boot `npm run dev` and open `http://localhost:3000/design-system`.
- [ ] T5.2 **Keyboard-only**: Tab to first ConsentDialog trigger → Enter → verify focus lands on **Refuse** → Tab cycles Refuse → Accept → close (X is hidden) → Refuse → … → ESC closes.
- [ ] T5.3 **Reduced motion**: DevTools → Rendering → Emulate `prefers-reduced-motion: reduce` → re-open dialog → animation collapses to ~0 ms.
- [ ] T5.4 **Mobile viewport** (DevTools at 375 × 667 px iPhone SE): dialog renders as **bottom sheet** with rounded top corners only. Internal scroll works if content overflows.
- [ ] T5.5 **VoiceOver iOS or NVDA Windows** (UX spec quarterly requirement; do at least once for this component): open dialog and confirm announcement = "Dialogue, [title]. [description]. Données concernées : … Durée : … Bénéficiaire : …".
- [ ] T5.6 **Contrast spot-check**: open destructive variant; verify the destructive button (`#9E2A24` / `#FAFAF7` background of viewport, or `bg-destructive-foreground` on `bg-destructive` for the button itself) is ≥ 4.5:1 — already enforced by Story 1.2 `contrast.test.ts` for the `danger on bg` pair, but worth re-checking on the actual rendered button.

### T6 — Documentation

- [ ] T6.1 Append a one-paragraph note to `docs/patterns/` (folder exists per Story 1.1) — file `consent-pattern.md` — describing **when to use** `ConsentDialog` vs an inline `<Checkbox>` (decision table: signup flow = checkbox; granular third-party access = ConsentDialog).
- [ ] T6.2 In the file header comment of `consent-dialog.tsx`, document the **three deferred items** (per §4.10 below): audit log wiring (Story 1.13), `axe-core` automated a11y test (cross-cutting story), `motion-narrative` ban rationale (Epic 4 reservation).

### T7 — Final validation

- [ ] T7.1 `cd apps/web && npm run typecheck` — clean.
- [ ] T7.2 `cd apps/web && npm run lint` — clean.
- [ ] T7.3 `cd apps/web && npm test -- --run` — all tests pass, count ≥ 18.
- [ ] T7.4 Visual: open `/design-system` → "Consent dialog" section → smoke-test the 4 demos as described in T5.
- [ ] T7.5 Open a PR with description noting: (a) no migrations, no backend changes; (b) all 4 demos visible at `/design-system#consent-dialog-heading`; (c) deferred items added to `deferred-work.md`.
- [ ] T7.6 Update `_bmad-output/implementation-artifacts/deferred-work.md` with the three deferred items (T6.2 list) under a new section "Deferred from: code review of 1-14-composant-consent-dialog ({date})".

### Review Findings (code review 2026-05-16)

Three adversarial layers ran: Blind Hunter (diff-only), Edge Case Hunter (diff + project), Acceptance Auditor (diff + spec). Findings consolidated below. Dismissed: 9 (false positives / by-design / works-in-current-env).

#### Decision needed

- [x] [Review][Decision] **Extend content-hash inputs to include `acceptLabel`, `refuseLabel`, `isAcceptDestructive`?** — Resolved option (b): canonical JSON extended from 5 to 8 fields. AC5 updated. New sensitivity tests added for title, `isAcceptDestructive`, and `acceptLabel`.

#### Patches (unchecked = to apply)

- [x] [Review][Patch] **P1 — Re-entry & async safety on Accept** [apps/web/src/components/ui/consent-dialog.tsx:110-120] — Wrap `handleAccept` in `try/catch/finally`. Add internal `isPendingRef` to prevent re-entry while hash + `onAccept` are in flight (mitigates rapid Accept→Refuse race and orphan `await` if consumer unmounts). Re-enable on rejection. Add Vitest test asserting that a rejecting `onAccept` does not freeze the component.
- [x] [Review][Patch] **P2 — ESC blocked during submit** [apps/web/src/components/ui/consent-dialog.tsx:127-130] — Pass `onEscapeKeyDown={(e) => isSubmitting && e.preventDefault()}` AND `onPointerDownOutside={(e) => isSubmitting && e.preventDefault()}` to `DialogPrimitive.Content`. Currently the `!isSubmitting` guard only skips `onRefuse` but still calls `onOpenChange(next)`, which lets the parent unmount the dialog mid-submit.
- [x] [Review][Patch] **P3 — `<li key>` index-prefixed to handle duplicate `dataMentioned`** [apps/web/src/components/ui/consent-dialog.tsx:146-148] — `key={`${index}-${item}`}` (current `key={item}` collides if two entries share the string; React duplicate-key warning + potential DOM-node reuse).
- [x] [Review][Patch] **P4 — iOS safe-area inset on mobile bottom-sheet** [apps/web/src/components/ui/consent-dialog.tsx:132] — Add `pb-[env(safe-area-inset-bottom)]` to the mobile classes. iPhone home-indicator currently overlaps the bottom buttons.
- [x] [Review][Patch] **P5 — a11y: `aria-busy` + screen-reader status during submit** [apps/web/src/components/ui/consent-dialog.tsx:124, 169-175] — Add `aria-busy={isSubmitting}` to `DialogPrimitive.Content` and render a visually-hidden `<span role="status" className="sr-only">Envoi en cours…</span>` when submitting. The spinner is `aria-hidden`; screen readers announce nothing today.
- [x] [Review][Patch] **P6 — Empty-string label fallback** [apps/web/src/components/ui/consent-dialog.tsx:87-88] — Use `acceptLabel || "Accepter"` / `refuseLabel || "Refuser"` instead of default parameters. Default-parameter syntax only applies on `undefined`, not `""`.
- [x] [Review][Patch] **P7 — Mobile sticky footer to keep CTAs above the fold** [apps/web/src/components/ui/consent-dialog.tsx:160] — On iPhone SE (320×568) with a long description + many bullet items, the buttons scroll below the fold inside the bottom-sheet. Wrap `<DialogFooter>` so it is `sticky bottom-0 bg-background pt-2` on mobile, normal on `sm:+`.
- [x] [Review][Patch] **P8 — Defensive focus fallback** [apps/web/src/components/ui/consent-dialog.tsx:127-130] — If `refuseButtonRef.current` is `null` (Strict Mode double-mount), focus is silently dropped and the trap is broken until Tab. Fall back to focusing the `DialogPrimitive.Content` element itself.
- [x] [Review][Patch] **P9 — Refuse path single-source-of-truth** [apps/web/src/components/ui/consent-dialog.tsx:105-108] — `handleRefuse` directly calls `onOpenChange(false)`, bypassing `handleOpenChange`. Today's tests pass because Radix only forwards `onOpenChange` on internal transitions, but the dual paths are fragile. Make `handleRefuse` call `handleOpenChange(false)` exclusively (drop the direct `onRefuse?.()` call there).
- [x] [Review][Patch] **P10 — Test: hash-sensitivity (different inputs → different hashes)** [apps/web/src/components/ui/consent-dialog.test.tsx] — The current determinism test would pass for a constant-returning hash function. Add an `it("contentHash is sensitive to inputs — title change yields different hash")` test.
- [x] [Review][Patch] **P11 — Doc + comment hygiene** [docs/patterns/consent-pattern.md:20 + apps/web/src/components/ui/consent-dialog.tsx:19-32] — (a) `consent-pattern.md` claims "Vitest test enforces equal size classes; this rule is encoded in CI" — the test only covers the default-rendered pair, not arbitrary variant combinations. Soften to "the default pair is verified in CI; non-default callers should keep `size='default'` on both". (b) The component header comment lists `axe-core deferred` and `motion-narrative banned` as adjacent bullets — the phrasing "reserved for Epic 4 graph" only applies to motion-narrative; clarify.
- [x] [Review][Patch] **P12 — Showcase section id consistency** [apps/web/src/app/design-system/page.tsx:435-437] — The section has `id="consent-dialog-heading"` (used by the URL anchor) and `aria-labelledby="consent-dialog-heading-label"` pointing to a separate id on the inner `<h2>`. Anchor still works, but the naming mismatch is confusing. Rename either to match (preserve the URL fragment).

#### Deferred (logged in `deferred-work.md`)

- [x] [Review][Defer] **No regression test for empty `dataMentioned`** [apps/web/src/components/ui/consent-dialog.test.tsx] — deferred, low-impact edge case; current implementation renders an empty `<ul>` without a label-only fallback. Worth covering when the component sees real production usage.

---

## 4. Dev Notes

### 4.1 Project context — what already exists

**Shipped (Stories 1.1 + 1.2):**

- `apps/web/src/components/ui/{button,card,dialog,form,input,label}.tsx` — shadcn primitives (`Dialog` is the **base** ConsentDialog composes).
- `apps/web/src/styles/tokens.css` + `tailwind.config.ts` — design tokens R1 Vermillon, type scale, spacing, motion, **global `prefers-reduced-motion` rule** (no need to re-implement reduced motion in this component).
- `apps/web/src/app/design-system/page.tsx` (+ `_components/dialog-demo.tsx`) — showcase page **already includes a `DialogDemo`** demonstrating the base shadcn Dialog. ConsentDialog adds **its own section** alongside, not replacing.
- `lucide-react` ^1.14 — icon library (`Loader2` for the in-flight spinner).
- `@radix-ui/react-dialog` ^1.1.15 — already a transitive dep of the shadcn Dialog primitive.
- `@testing-library/react` ^16.1 + `@testing-library/user-event` (Story 1.1 stack — confirm `user-event` is in deps; if not, `npm install --save-dev @testing-library/user-event`).
- `vitest` ^2.1 with JSDOM environment — Web Crypto API is available (`crypto.subtle.digest` polyfill provided by Node 20+).

**Does not exist yet (this story creates):**

- `apps/web/src/components/ui/consent-dialog.tsx`
- `apps/web/src/components/ui/consent-dialog.test.tsx`
- `apps/web/src/app/design-system/_components/consent-dialog-demos.tsx`
- `docs/patterns/consent-pattern.md`

### 4.2 Architecture decisions locked (cf. Stories 1.1 / 1.2 / 1.3)

| Decision | Locked choice | Source |
|---|---|---|
| Component library | shadcn/ui copied locally (not npm dep) | Architecture §Frontend |
| Component path for composite Couche 3 | `apps/web/src/components/ui/<name>.tsx` (colocated with shadcn primitives — see §4.3 below) | This story |
| Form library | React Hook Form + Zod — **not used here** (no form), but consumer call sites may wrap consent inside RHF | Architecture |
| Motion durations | Use tokens `duration-instant / quick / standard / narrative`; **narrative reserved for Epic 4 graph** | Story 1.2 |
| Reduced motion | Global rule in `tokens.css` — nothing to do per-component | Story 1.2 |
| Hash algorithm for content immutability proof | **SHA-256 via Web Crypto API** (`window.crypto.subtle.digest`) — zero new deps | This story |
| Internationalisation | French hard-coded strings via props (callers own copy); next-intl wiring = Story 7.7 | Story 1.3 §4.2 |
| Locale attribute | `<html lang="fr">` already set by Story 1.1 layout | Story 1.1 |
| Test framework | Vitest (front) | Story 1.1 |
| TS strictness | `tsconfig.json` strict — every prop typed, no `any` | Story 1.1 |
| File naming | `kebab-case.tsx` | shadcn convention |

### 4.3 Why `components/ui/` and not `components/features/consent/`

The architecture `project-structure-boundaries.md` plans `components/features/<feature>/...` for **feature-scoped** composites (`features/onboarding/`, `features/recommendations/`). ConsentDialog is **cross-feature** — consumed by parental opt-in (1.4), revocation (1.10), account deletion (1.12), paywall (5.3), counselor consent (6.7). Placing it in `features/<feature>/` would arbitrarily privilege one consumer. Placing it in `components/ui/` is correct because:

- It composes shadcn primitives (the philosophy of shadcn is to customise primitives in your own `components/ui/`).
- It is reusable across the entire app.
- The UX spec § Component Implementation Strategy says: "Tous les composants couche 3 dans **un seul dossier** → audit visuel en 1 minute" — colocating with `ui/` satisfies this until volume justifies a dedicated `components/path-advisor/` directory (likely Sprint 3+ when 5+ Couche 3 components exist).

**Decision:** ship to `components/ui/consent-dialog.tsx`. **Re-evaluate at Story 3.11** (`ScoreVocationnel`) — if `ui/` is becoming crowded, split into `components/path-advisor/` then.

### 4.4 Why ESC = refuse, not "neutral close"

UX spec § Overlay Patterns says "Échap pour fermer". For a **consent capture**, an ambiguous close (user pressed ESC, did they accept? refuse? defer?) is the worst outcome — it leaves the calling feature in a guessing state and the audit log without a decision. The unambiguous interpretation: **ESC = refuse**. This matches GDPR Article 7 expectations ("withdrawing consent must be as easy as giving it") — ESC is the user's easiest withdrawal path.

**Implication:** the caller's `onRefuse` handler must be **idempotent** and should NOT trigger destructive side-effects (e.g., do not pre-emptively revoke other permissions on refuse — just record the refusal).

### 4.5 Suppressing the auto-injected `X` close button — exact JSX

The shadcn `DialogContent` shipped in Story 1.2 ([dialog.tsx:32-54](apps/web/src/components/ui/dialog.tsx#L32-L54)) embeds `<DialogPrimitive.Close className="absolute right-4 top-4 …"><X /></DialogPrimitive.Close>` inside its `Content`. ConsentDialog must hide this without forking the primitive. Two approaches:

**Approach A (preferred — clean separation):** in `consent-dialog.tsx`, do **not** use the wrapper `<DialogContent>`. Instead, recompose its internals (Portal + Overlay + Content) without the auto-injected `<X>`:

```tsx
import * as DialogPrimitive from "@radix-ui/react-dialog";
import { Dialog, DialogPortal, DialogOverlay } from "@/components/ui/dialog";
// DialogHeader, DialogFooter, DialogTitle, DialogDescription remain shadcn

// inside the component render:
<Dialog open={open} onOpenChange={handleOpenChange}>
  <DialogPortal>
    <DialogOverlay />
    <DialogPrimitive.Content
      onOpenAutoFocus={(e) => { e.preventDefault(); refuseButtonRef.current?.focus(); }}
      className={cn(
        // mobile bottom-sheet
        "fixed bottom-0 left-0 right-0 z-50 grid w-full gap-4 border bg-background p-6 shadow-lg max-h-[90vh] overflow-y-auto rounded-t-lg",
        // desktop modal — overrides above at sm+
        "sm:left-1/2 sm:top-1/2 sm:bottom-auto sm:right-auto sm:-translate-x-1/2 sm:-translate-y-1/2 sm:max-w-lg sm:rounded-lg",
        // motion
        "data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 duration-quick",
      )}
    >
      <DialogHeader>…</DialogHeader>
      <section>…</section>
      <DialogFooter>
        <Button ref={refuseButtonRef} variant="outline" …>{refuseLabel ?? "Refuser"}</Button>
        <Button variant={isAcceptDestructive ? "destructive" : "default"} …>{acceptLabel ?? "Accepter"}</Button>
      </DialogFooter>
    </DialogPrimitive.Content>
  </DialogPortal>
</Dialog>
```

This bypasses the shipped `DialogContent` wrapper but reuses `DialogPortal`, `DialogOverlay`, and the structural primitives. No change to `dialog.tsx`.

**Approach B (rejected):** modify `dialog.tsx` to make the X opt-in via a prop. Rejected because shadcn's philosophy is to keep primitives unmodified once copied — diverging now would compound at every story that touches Dialog.

### 4.6 Why hash on the client, not the server

Audit log immutability (FR12) is server-side concern; the **hash is a client-computed digest of what the user saw** at the moment of consent. The client is the only place that has direct access to the rendered DOM. If the server were to compute the hash, it would have to receive the canonical JSON and trust that it matches what was shown — defeating the integrity purpose.

The hash will be **stored alongside** the audit entry (Story 1.13 will receive `contentHash` as part of the audit row). It is the proof that "the user accepted *this exact* content" — if the policy text or beneficiary list later changes in code, old audit entries still reference the original hash and are forensically defendable.

### 4.7 Why both buttons need same size class (no dark pattern in detail)

GDPR Article 7(2) (and the EU EDPB guidance on consent) requires that withdrawing/refusing consent be **as easy** as accepting. UI patterns where the accept button is large/colourful and the refuse is small/grey ("cookie banner from hell") violate this. By enforcing **identical `size="default"`** classes and asserting it in a Vitest test, we lock the rule at the codebase level — any future redesign that tries to shrink the refuse button will fail CI.

### 4.8 Component scope — what this story does NOT do

- **No audit log POST** — the caller wires `onAccept(meta)` to its own audit endpoint when one exists. Story 1.13 will introduce the endpoint; until then, callers can `console.info(meta)` or POST to a placeholder. This component is **pure UI**.
- **No state persistence** — the dialog is controlled (`open` / `onOpenChange` from the caller). No internal localStorage, no memoisation of past decisions. Persistence belongs to the consuming feature.
- **No revocation list rendering** — Story 1.9 (`PermissionList`) will render the list; ConsentDialog is one-shot per consent event.
- **No automated `axe-core` test** — `axe-core` is not yet in `apps/web` deps; adding it is a cross-cutting concern bigger than this story. Track in `deferred-work.md`.
- **No internationalisation framework** — strings are caller-provided in French. `next-intl` wiring is Story 7.7.

### 4.9 Versions and libraries to use

| Library | Version (per `apps/web/package.json`) | Usage |
|---|---|---|
| `react` | 19.2.4 | functional component, hooks (`useRef`, `useState`) |
| `next` | 16.2.6 | App Router, Server vs Client component split (showcase page is Server; `_components/consent-dialog-demos.tsx` is Client) |
| `@radix-ui/react-dialog` | ^1.1.15 | primitive `Dialog`, `Portal`, `Overlay`, `Content` |
| `lucide-react` | ^1.14 | `Loader2` icon for in-flight state |
| `class-variance-authority` | ^0.7.1 | indirect (used inside `Button`) |
| `tailwind-merge` + `clsx` | ^3.6 + ^2.1 | composed into `cn` helper from `@/lib/utils` |
| `@testing-library/react` | ^16.1 | unit tests (uses `render`, `screen`, `fireEvent`, `act`, `waitFor`) |
| `vitest` | ^2.1 | test runner |

**No new dependency required.** `@testing-library/user-event` is intentionally **not** added — `fireEvent` from `@testing-library/react` covers the ESC keypress and button clicks needed by AC7. If a future story needs realistic typing (e.g., signup form keystroke-by-keystroke testing in 1.3), `user-event` can be added then.

### 4.10 Items to defer to `deferred-work.md` after merge

Three items must land in `_bmad-output/implementation-artifacts/deferred-work.md` under a fresh section:

1. **Audit log wiring** — `onAccept(meta)` does not yet POST to `/api/v1/me/consents` or equivalent. Each consuming story (1.4, 1.10, 1.12, 5.3, 6.7) must wire its own POST. Endpoint contract finalised in Story 1.13.
2. **`axe-core` automated a11y test** — not in deps yet; ConsentDialog relies on Radix's a11y guarantees + manual screen-reader QA per AC4 / T5.5. Add a cross-cutting "axe-core CI gate" story when the second Couche 3 component lands.
3. **Storybook (or equivalent isolation viewer)** — the UX spec recommends Storybook per Couche 3 component; we substitute the `/design-system` showcase for MVP. Re-evaluate at Sprint 4+ when 4-5 Couche 3 components exist.

### 4.11 Open questions for code review

None blocking. The component scope is tight and the AC are deterministic. The only judgment calls are §4.3 (path location) and §4.4 (ESC = refuse), both documented inline.

---

## Project Structure Notes

**New files (4):**

```
apps/web/src/components/ui/consent-dialog.tsx           # the component
apps/web/src/components/ui/consent-dialog.test.tsx      # Vitest unit tests
apps/web/src/app/design-system/_components/consent-dialog-demos.tsx  # showcase client component
docs/patterns/consent-pattern.md                        # when-to-use guide
```

**Modified files (2):**

```
apps/web/src/app/design-system/page.tsx                 # add ConsentDialog section
_bmad-output/implementation-artifacts/deferred-work.md  # append three deferred items
```

**Unchanged (no regression risk):**

- `apps/web/src/components/ui/dialog.tsx` — DO NOT modify; ConsentDialog recomposes its primitives (per §4.5 Approach A).
- `apps/web/src/styles/tokens.css` — no new tokens required; existing `duration-quick` and `prefers-reduced-motion` rule suffice.
- `tailwind.config.ts` — no new utilities.
- `apps/api/**` — backend untouched.

**Variance from the planned `project-structure-boundaries.md`:** that document anticipates `components/features/` but does not specify a path for cross-feature Couche 3 composites. We resolve by colocating with `components/ui/` and documenting in §4.3. Revisit at Sprint 3+.

---

## References

- **Epic 1, Story 1.14 definition:** [_bmad-output/planning-artifacts/epics/epic-1-foundation-auth-multi-role-rbac-conformite-rgpd-infra-technique.md#L338-L361](_bmad-output/planning-artifacts/epics/epic-1-foundation-auth-multi-role-rbac-conformite-rgpd-infra-technique.md#L338-L361)
- **UX-DR11 `ConsentDialog`:** [_bmad-output/planning-artifacts/ux-design-specification.md#L1171](_bmad-output/planning-artifacts/ux-design-specification.md#L1171)
- **UX-DR26 "ConsentDialog: Sheet bottom mobile / Modal centered desktop":** [_bmad-output/planning-artifacts/ux-design-specification.md#L1444](_bmad-output/planning-artifacts/ux-design-specification.md#L1444)
- **UX risk note "ConsentDialog trop complexe pour un solo founder":** [_bmad-output/planning-artifacts/ux-design-specification.md#L1229](_bmad-output/planning-artifacts/ux-design-specification.md#L1229)
- **No-dark-pattern button hierarchy:** [_bmad-output/planning-artifacts/ux-design-specification.md#L1242](_bmad-output/planning-artifacts/ux-design-specification.md#L1242)
- **Accessibility strategy (RGAA AA, focus, screen reader):** [_bmad-output/planning-artifacts/ux-design-specification.md#L1446-L1511](_bmad-output/planning-artifacts/ux-design-specification.md#L1446-L1511)
- **FR9 (revocation) and FR12 (audit log) requirements:** [_bmad-output/planning-artifacts/prd/functional-requirements.md](_bmad-output/planning-artifacts/prd/functional-requirements.md)
- **Architecture — audit log table contract:** [_bmad-output/planning-artifacts/architecture/core-architectural-decisions.md#L32](_bmad-output/planning-artifacts/architecture/core-architectural-decisions.md#L32)
- **Architecture — `apps/accounts/services/consent_service.py` planned location** (out of scope, future endpoint): [_bmad-output/planning-artifacts/architecture/project-structure-boundaries.md#L155](_bmad-output/planning-artifacts/architecture/project-structure-boundaries.md#L155)
- **Story 1.2 — design tokens (motion, contrast, reduced-motion rule):** [_bmad-output/implementation-artifacts/1-2-design-system-tokens.md](_bmad-output/implementation-artifacts/1-2-design-system-tokens.md)
- **Existing `Dialog` primitive (to recompose, not modify):** [apps/web/src/components/ui/dialog.tsx](apps/web/src/components/ui/dialog.tsx)
- **Existing `/design-system` showcase to extend:** [apps/web/src/app/design-system/page.tsx](apps/web/src/app/design-system/page.tsx)

---

## Dev Agent Record

### Agent Model Used

_(to be filled by dev agent)_

### Debug Log References

_(to be filled by dev agent)_

### Completion Notes List

_(to be filled by dev agent)_

### File List

_(to be filled by dev agent)_
