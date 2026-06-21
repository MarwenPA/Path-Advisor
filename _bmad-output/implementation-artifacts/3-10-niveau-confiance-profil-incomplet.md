# Story 3.10: Niveau de confiance affiché sur les recos en profil incomplet

**Epic:** 3 — Recommandation Vocationnelle (Premier Aha)
**Status:** review
**Sprint:** 6 (Recommandation vocationnelle)
**Story Key:** `3-10-niveau-confiance-profil-incomplet`
**Estimation:** S — front-only pour l'essentiel (SignauxDrawer + override backend bulletins).

---

## 1. User Story

**As a** élève Léa qui n'a pas encore ajouté ses bulletins,
**I want** comprendre que mes recos sont indicatives sans pour autant me sentir "cas spécial",
**So that** je peux explorer le produit avec dignité et savoir ce qui s'enrichira en complétant mon profil (FR26 + UX-DR25).

---

## 2. Acceptance Criteria (BDD)

### AC1 — Affichage identique profil complet / incomplet

**Given** mon profil est incomplet (sans bulletins)
**When** je consulte mes recos vocationnelles
**Then** la structure visuelle est strictement identique à celle d'un profil complet
**And** chaque score affiche un label discret "indicatif" en `text-caption text-text-muted` (pas en rouge, pas en alerte)

### AC2 — Contexte factuel dans l'explicabilité

**Given** je tape sur une carte métier
**When** je consulte l'explicabilité (SignauxDrawer / Story 3.6)
**Then** je vois les signaux + un message factuel :
  "Avec tes bulletins, on pourrait préciser ton score à ±5 pts près au lieu de ±15 actuellement"
**And** un CTA discret propose "Ajouter mes bulletins" (1 tap pour ouvrir BulletinsAddSheet)

### AC3 — Conformité émotionnelle

**Given** je suis Léa
**When** je navigue sur les recos
**Then** je ne vois JAMAIS de message culpabilisant ("Tu manques de données" / "Profil insuffisant")
**And** la posture est : voilà ce qu'on a, voilà ce qui s'ajouterait. Choix libre.

### AC4 — confidence_level garanti côté backend

**Given** un élève sans bulletins
**When** le moteur calcule ses recos
**Then** chaque profession retournée a `confidence_level = "low"` quelle que soit la réponse de l'AI service
**And** un élève avec bulletins garde la valeur renvoyée par l'AI service (ou "medium" par défaut)

---

## 3. Tasks / Subtasks

### T1 — Backend: override confidence_level selon has_bulletins

- [x] Modifier `apps/api/apps/recommendations/services/recommendation_service.py`
- [x] Après réception de la réponse AI service : si `has_bulletins=False` → forcer `confidence_level="low"` sur chaque scored_occupation
- [x] Si `has_bulletins=True` et ai-service retourne null/absent → fallback `"medium"`
- [x] Tests pytest : `has_bulletins=False` → all `"low"` ; `has_bulletins=True` → valeur ai-service préservée

### T2 — Frontend: SignauxDrawer context block pour profil incomplet

- [x] Ajouter `confidenceLevel?: "low" | "medium" | "high"` à `SignauxDrawerProps`
- [x] Quand `"low"` : afficher après la liste des signaux un bloc contextuel discret :
  - [x] Message factuel (±5 vs ±15 pts)
  - [x] CTA "Ajouter mes bulletins" → ouvre `BulletinsAddSheet`
  - [x] Styling : `text-body-sm text-text-muted`, fond neutre, jamais rouge ni warning
- [x] Tests Vitest : bloc visible quand `"low"`, absent quand `"medium"` / `"high"` / `undefined`

### T3 — Frontend: propager confidenceLevel dans MetiersList et FicheMetierClient

- [x] `MetiersList.tsx` : passer `drawerProfession?.confidence_level` à `<SignauxDrawer>`
- [x] `FicheMetierClient.tsx` : accepter et passer `confidenceLevel` (depuis `FicheMetierProps`) à `<SignauxDrawer>` (mapper `"indicative"` → `"low"`, `"normal"` → `"high"`)
- [x] Tests : spy/mock SignauxDrawer reçoit la bonne prop

### T4 — Frontend: empty state MetiersList non-culpabilisant

- [x] Remplacer "Aucune recommandation disponible... Complète ton profil pour obtenir tes premières suggestions." par un message neutre et factuel
- [x] AC3 : jamais de "manque de données" / "profil insuffisant"

---

## 4. Dev Notes

### Architecture existante (déjà en place)

- `confidence_level: "low" | "medium" | "high"` déjà dans `ScoredProfession` (recommendations.ts)
- `mapConfidence()` dans `MetiersList.tsx` : `"low"` → `"indicative"`, rest → `"normal"`
- `ScoreVocationnel` rend déjà le label "indicatif" quand `confidenceLevel === "indicative"`
- `BulletinsAddSheet` : composant existant à réutiliser pour le CTA
- `FicheMetierClient` parse déjà `confidence` depuis l'URL et mappe vers `"indicative"` / `"normal"`

### Règle émotionnelle non-négociable (UX-DR25)

Aucun message dans la codebase ne doit mentionner "manque de données", "profil insuffisant", ou suggérer que l'élève est en-dessous d'un standard. La posture est toujours additive : "avec tes bulletins, voilà ce qui s'ajouterait".

### Intégration BulletinsAddSheet dans SignauxDrawer

`SignauxDrawer` est un composant "use client". Il peut manager un état `bulletinsSheetOpen` localement pour ouvrir `BulletinsAddSheet` sans prop-drilling.

---

## 5. Dev Agent Record

### Agent Model Used
claude-sonnet-4-6

### Completion Notes List
- T1: Override `confidence_level` dans `recommendation_service.py` — si `has_bulletins=False` on force `"low"`, sinon on préserve la valeur AI ou fallback `"medium"`. 3 nouveaux tests pytest couvrent les 3 cas.
- T2: Nouveau composant `IncompleteProfileContext` dans `SignauxDrawer.tsx` — factuel, non-culpabilisant, intègre `BulletinsAddSheet` via état local `bulletinsSheetOpen`. 5 nouveaux tests Vitest.
- T3: `MetiersList.tsx` passe `drawerProfession?.confidence_level` à `<SignauxDrawer>`. `FicheMetierClient.tsx` mappe `"indicative"` → `"low"` / `"normal"` → `"high"` via `toDrawerConfidence`. 2 nouveaux tests Vitest de propagation.
- T4: Empty state `MetiersList` remplacé par "Tes premières recommandations apparaîtront ici bientôt." avec `data-testid="metiers-empty"`. Test AC3 mis à jour.
- Suite complète : 511 tests, 508 passent (3 échecs préexistants step-3 onboarding, non liés à 3.10).

### File List
- `apps/api/apps/recommendations/services/recommendation_service.py` — override confidence_level
- `apps/api/apps/recommendations/tests/test_recommendations.py` — 3 nouveaux tests T1
- `apps/web/src/components/professions/SignauxDrawer.tsx` — IncompleteProfileContext + BulletinsAddSheet
- `apps/web/src/components/professions/__tests__/SignauxDrawer.test.tsx` — 5 nouveaux tests T2
- `apps/web/src/app/(authenticated)/mes-metiers/MetiersList.tsx` — propagation + empty state
- `apps/web/src/app/(authenticated)/mes-metiers/__tests__/MetiersList.test.tsx` — 3 tests T3/T4
- `apps/web/src/app/(authenticated)/metiers/[slug]/FicheMetierClient.tsx` — toDrawerConfidence mapper

### Change Log
- 2026-06-21 — Story 3.10 créée pour implémentation.
- 2026-06-21 — T1 implémenté : override confidence_level dans recommendation_service.py + 3 tests pytest.
- 2026-06-21 — T2 implémenté : IncompleteProfileContext dans SignauxDrawer + BulletinsAddSheet CTA + 5 tests Vitest.
- 2026-06-21 — T3 implémenté : propagation confidenceLevel MetiersList + FicheMetierClient + 2 tests Vitest.
- 2026-06-21 — T4 implémenté : empty state non-culpabilisant MetiersList.
- 2026-06-21 — Tous les ACs validés, suite : 508/511 passent (3 échecs préexistants non liés).
