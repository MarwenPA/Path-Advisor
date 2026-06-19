# ProfileMaturityIndicator

Story 2.7 — Indicateur qualitatif de maturité de profil (3 états).

## Principle

**Never a percentage.** This component replaces the classic "Profile X% complete" pattern (Diplomeo, LinkedIn) which induces guilt. Instead: three qualitative states describing what the user **unlocks**, not what they **lack**.

## API

```tsx
import { ProfileMaturityIndicator } from "@/components/features/profile/profile-maturity-indicator";
```

```ts
type MaturityLevel = 'base' | 'enriched' | 'complete';

type MaturityNextAction = {
  label: string;       // action label — gain-framing only
  benefit: string;     // concrete benefit ("Tu débloques...")
  onClick: () => void; // opens the relevant flow sheet
  icon: 'bulletins' | 'level' | 'passions' | 'specialites';
};

type ProfileMaturityIndicatorProps = {
  level: MaturityLevel;
  nextActions: readonly MaturityNextAction[];
  variant?: 'profile-header' | 'dashboard-card' | 'inline-compact';
  showCallToAction?: boolean;
};
```

**IMPORTANT:** No `percentage: number` or `progress: 0..100` prop — forbidden by construction.

## Variants

### `profile-header` (default) — Story 2.6 profile page

Full card with level label, description, and expandable action list.

```tsx
<ProfileMaturityIndicator
  level={maturity.level}
  nextActions={buildNextActions(maturity.next_actions, { openBulletins, openPassions })}
  variant="profile-header"
/>
```

### `dashboard-card` — Epic 3 dashboard

Compact horizontal row. **Returns `null` when `level === 'complete'`** (anti-noise).

```tsx
<ProfileMaturityIndicator
  level={maturity.level}
  nextActions={[]}
  variant="dashboard-card"
/>
```

### `inline-compact` — contextual pages

Pill chip with tooltip. Navigates to `/profile` on click.

```tsx
<ProfileMaturityIndicator level={maturity.level} nextActions={[]} variant="inline-compact" />
```

## Level copy (locked — validated with Léa/Mehdi proxies)

| Level | Label | Description |
|---|---|---|
| `base` | "Profil de base" | "Tu as l'essentiel pour des recos indicatives — toutes les explorations sont ouvertes." |
| `enriched` | "Profil enrichi" | "Tu débloques les stats personnalisées sur tes parcours." |
| `complete` | "Profil complet" | "Tu profites de toutes les features — recos affinées, stats précises, parcours ciblés." |

## Forbidden words (enforced at runtime in dev)

The following strings trigger `console.warn` if they appear in any `nextAction.label` or `nextAction.benefit`:

```
incomplet, incomplète, manque, manquant, manquante, %, pourcentage,
raté, ratée, tu rates, il te reste, tu n'as pas encore,
termine ton profil, complète ton profil, finalise
```

Write actions as **gains**: "Tu débloques X", "Tes recos deviennent plus précises".
Never as **deficits**: "Il te manque tes bulletins", "Tu n'as pas complété".

## Data fetching

```tsx
import { useMaturityLevel } from "@/hooks/use-maturity-level";

const { data: maturity } = useMaturityLevel(userId);
```

Endpoint: `GET /api/v1/students/me/profile/maturity` → `{ level, next_actions, computed_at }`

## Level-up celebration (AC8)

```tsx
import { useMaturityCelebration } from "@/hooks/use-maturity-celebration";

const { message, dismiss } = useMaturityCelebration(maturity?.level, userId);
// If message != null → show a transient success toast (3s auto-dismiss)
// On downgrade → message is always null (silence respectueux)
```

Toast rules:
- Success color (`color-success` / `#2F6B4F`)
- 3 s auto-dismiss
- No confetti, no modal, no "Bravo !"
- Fires at most once per transition (sessionStorage + server flag)
