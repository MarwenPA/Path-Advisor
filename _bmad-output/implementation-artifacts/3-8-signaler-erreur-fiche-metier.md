# Story 3.8: Signaler une erreur ou information obsolète sur une fiche métier

**Epic:** 3 — Recommandation Vocationnelle (Premier Aha)
**Status:** review
**Sprint:** 6 (Recommandation vocationnelle)
**Story Key:** `3-8-signaler-erreur-fiche-metier`
**Estimation:** S (small) — formulaire compact + endpoint backend + audit log. Front léger, backend simple. Sized ~1 j focused work.

> Mécanisme de community sourcing pour maintenir le référentiel à jour. L'élève peut signaler une erreur sur une fiche métier ; le signalement est enregistré et placé dans la file de modération admin (Epic 9). Indépendant du moteur de scoring — peut être développé avant que les stories de scoring soient prêtes.

---

## 1. User Story

**As a** élève ou utilisateur attentif,
**I want** signaler une erreur ou information obsolète sur une fiche métier,
**So that** le référentiel reste à jour grâce au community sourcing (FR24), et que le produit gagne en crédibilité par la qualité de ses données.

**Business value :** sans ce mécanisme, les erreurs dans les 50 métiers seed ne remontent jamais. Avec ce mécanisme, les élèves deviennent des contributeurs de qualité — et la confiance dans les fiches augmente.

---

## 2. Acceptance Criteria (BDD)

### AC1 — Point d'entrée : bouton "Signaler une erreur" en pied de fiche

**Given** je suis sur une fiche métier (`FicheMetier` composant Story 3.12)
**When** je consulte le bas de la fiche
**Then** je vois un bouton tertiary discret "Signaler une erreur" avec icône Lucide `Flag` (taille `sm`, `color-text-subtle`)
**And** ce bouton est toujours visible, pas masqué derrière un accordéon

**And** le bouton n'est pas affiché en `variant="print"` (pas de CTA interactif en impression)

### AC2 — Formulaire de signalement (bottom sheet mobile / dialog desktop)

**Given** je tape sur "Signaler une erreur"
**When** le formulaire s'ouvre
**Then** sur mobile : bottom sheet (slide-up) avec handle de glissement
**And** sur desktop : dialog centré (shadcn `Dialog`)
**And** le formulaire contient :
- **Titre** : "Signaler une erreur sur cette fiche" (h2 dans le dialog)
- **Sous-titre** : nom de la profession pré-rempli en `text-body-muted`
- **Type d'erreur** (Select shadcn, obligatoire) : 4 options
  - "Description inexacte ou trompeuse"
  - "Débouchés ou informations périmées"
  - "Lien ou ressource cassé(e)"
  - "Autre"
- **Localisation précise** (Input texte, optionnel) : placeholder "Ex. : section 'Comment y aller', paragraphe 2"
- **Commentaire** (Textarea, optionnel, max 500 chars) : placeholder "Décris l'erreur ou propose une correction"
- **Bouton primary** "Envoyer le signalement" + **bouton tertiary** "Annuler"

**And** le Select "Type d'erreur" est le seul champ obligatoire — les autres sont optionnels

### AC3 — Soumission et feedback

**Given** je sélectionne un type d'erreur et clique "Envoyer le signalement"
**When** la soumission est envoyée
**Then** le formulaire se ferme
**And** un toast 4 s confirme : "Merci, ton signalement a été pris en compte"
**And** le bouton "Signaler une erreur" sur la fiche passe en état `reported` (icône `Flag` + label "Signalé", `color-text-muted`, non cliquable — un seul signalement par fiche par session)

**Given** une erreur réseau lors de la soumission
**When** la requête échoue
**Then** le formulaire reste ouvert
**And** un message d'erreur inline s'affiche sous le bouton primary : "Envoi échoué — réessaie dans quelques instants"
**And** le bouton primary revient à l'état normal (pas de double-submit)

### AC4 — Backend : endpoint POST signalement

**Given** l'API Django est déployée
**When** un élève authentifié envoie `POST /api/v1/professions/{slug}/reports/`
**Then** le payload est validé :
  ```json
  {
    "error_type": "description_inexacte | debouches_perimes | lien_casse | autre",
    "location": "string | null",
    "comment": "string (max 500 chars) | null"
  }
  ```
**And** un enregistrement `ProfessionReport` est créé avec :
  - `id` UUID
  - `profession_id` FK
  - `reporter_id` FK (student)
  - `error_type`
  - `location` (nullable)
  - `comment` (nullable)
  - `status` : `"pending"` (valeur initiale)
  - `created_at`

**And** la réponse est `201 Created` avec `{ "id": "...", "status": "pending" }`

**And** un utilisateur non authentifié reçoit `401 Unauthorized`

**And** RLS (Story 1.8) appliqué : un élève ne voit que ses propres signalements, pas ceux des autres

### AC5 — Audit log

**Given** un signalement est créé
**When** l'événement est loggué (Story 1.13)
**Then** l'audit log contient : `event: "profession_report_created"`, `{ profession_slug, error_type, reporter_id, report_id }`

### AC6 — File d'attente admin (Epic 9 — interface, pas ici)

**Given** un signalement est en `status: "pending"`
**When** l'admin consulte sa file (Epic 9)
**Then** il voit les signalements en attente triés par `created_at DESC`

**Note** : l'interface admin de traitement est hors scope de cette story (Epic 9). Cette story ne crée que l'endpoint de lecture admin minimaliste.

**Given** l'admin appelle `GET /api/v1/admin/professions/reports/`
**When** la réponse arrive
**Then** il voit la liste paginée des signalements en `status: "pending"` (permission `IsAdminUser`)

### AC7 — Notification optionnelle à résolution (Epic 9 — différé)

> Hors scope Sprint 6 — à implémenter en Epic 9 côté admin.

**Given** l'admin résout un signalement (Story 9.x)
**When** il clique "Résolu" ou "Fiche mise à jour"
**Then** l'élève reçoit (si opt-in notifications) : "La fiche que tu as signalée a été mise à jour"

### AC8 — Accessibilité

**Given** le formulaire de signalement est ouvert
**When** je le parcours au clavier
**Then** le focus est trapé dans le dialog/bottom-sheet (`focus-trap`)
**And** `Escape` ferme le formulaire (sans soumettre)
**And** l'ordre de focus : titre → Select type → Input localisation → Textarea → bouton Envoyer → bouton Annuler
**And** le Select a un `<label>` associé (`htmlFor`)
**And** le toast de confirmation est annoncé par `aria-live="polite"`

### AC9 — Tests

**Given** les tests tournent (Vitest + RTL + pytest)
**When** tous les tests passent
**Then** :
- **Frontend** :
  - Tap "Signaler une erreur" → formulaire ouvert
  - Soumission sans type d'erreur → champ en erreur, pas de submit
  - Soumission avec type → `POST /api/v1/professions/{slug}/reports/` appelé + toast affiché
  - Erreur réseau → message erreur inline, formulaire reste ouvert
  - `Escape` → formulaire fermé
  - Après soumission → bouton en état `reported`
  - Variant `print` → bouton "Signaler" absent
- **Backend** :
  - `POST` avec payload valide → 201 + `ProfessionReport` créé
  - `POST` avec `error_type` absent → 400
  - `POST` sans auth → 401
  - `POST` avec `comment` > 500 chars → 400
  - `GET /api/v1/admin/professions/reports/` → 403 pour élève, 200 pour admin
  - Audit log créé à chaque signalement

---

## 3. Tasks / Subtasks

### T1 — Backend : modèle + endpoint

- [x] Modèle `ProfessionReport` dans `apps/api/apps/professions/models.py`
- [x] Migration `0003_profession_report.py`
- [x] Serializer `ProfessionReportSerializer` (création + lecture admin)
- [x] Vue `ProfessionReportCreateView` (`POST /api/v1/professions/{slug}/reports/`)
- [x] Vue `ProfessionReportAdminListView` (`GET /api/v1/admin/professions/reports/`)
- [x] Audit log Story 1.13 : `profession_report_created`
- [x] RLS Story 1.8 appliqué (IsAuthenticatedAndActive + IsStudent)

### T2 — Frontend : composant `ReportErrorButton` + formulaire

- [x] Créer `apps/web/src/components/professions/ReportErrorButton.tsx`
  - Props : `{ professionSlug, professionName }`
  - État local : `open: boolean`, `reported: boolean`
- [x] Sous-composant `ReportErrorForm.tsx` (formulaire interne, utilisé dans Dialog / BottomSheet)
- [x] Hook `useReportProfessionError(slug)` — TanStack Query mutation
- [x] Intégration dans `FicheMetier.tsx` (Story 3.12) en pied de fiche (via prop ou composition)

### T3 — Tests

**Backend (pytest) :**
- [x] POST valide → 201 + audit log
- [x] POST sans `error_type` → 400
- [x] POST sans auth → 401
- [x] POST `comment` > 500 chars → 400
- [x] GET admin list → 200 pour admin, 403 pour élève

**Frontend (Vitest + RTL) :**
- [x] Tous les cas AC9 frontend (18 tests)

---

## 4. Dev Notes

### 4.1 Wireframe ASCII — formulaire mobile (bottom sheet)

```
┌───────────────────────────────────────────┐
│              ——— (handle)                 │
│  Signaler une erreur sur cette fiche      │ ← h2
│  Infirmier·ère de bloc opératoire         │ ← text-body-muted
│                                           │
│  Type d'erreur *                          │
│  ┌─────────────────────────────────────┐  │
│  │  Description inexacte ou trompeuse ▼│  │ ← Select shadcn
│  └─────────────────────────────────────┘  │
│                                           │
│  Où exactement ? (optionnel)              │
│  ┌─────────────────────────────────────┐  │
│  │  Ex. : section 'Comment y aller'…   │  │ ← Input
│  └─────────────────────────────────────┘  │
│                                           │
│  Commentaire (optionnel)                  │
│  ┌─────────────────────────────────────┐  │
│  │                                     │  │ ← Textarea 3 lignes
│  │                                     │  │
│  └─────────────────────────────────────┘  │
│                                  0/500    │
│                                           │
│  ┌─────────────────────────────────────┐  │
│  │   Envoyer le signalement            │  │ ← primary
│  └─────────────────────────────────────┘  │
│         Annuler                           │ ← tertiary
└───────────────────────────────────────────┘
```

### 4.2 États du bouton "Signaler une erreur"

| État | Label | Icône | Couleur | Cliquable |
|---|---|---|---|---|
| Default | "Signaler une erreur" | `Flag` | `color-text-subtle` | Oui |
| Loading | "Envoi…" | spinner | `color-text-subtle` | Non |
| Reported | "Signalé" | `Flag` filled | `color-text-muted` | Non |

### 4.3 Décisions design verrouillées

- **Un seul signalement par session** (pas par élève — pas de contrainte UNIQUE côté DB, c'est l'état front qui bloque le re-submit). Si l'élève revient sur la fiche après refresh, il peut re-signaler.
- **Formulaire minimaliste** — 1 champ obligatoire, 2 optionnels. Pas de screenshot upload, pas de formulaire long.
- **Bottom sheet mobile** (pas dialog) — cohérent avec les patterns mobile de l'app
- **Pas de confirmation admin en sprint 6** — la notif de résolution est différée à Epic 9

### 4.4 Items à différer

- Notification élève à résolution du signalement (Epic 9)
- Interface admin de traitement des signalements (Epic 9)
- Rate limiting par élève (protection spam) — à ajouter en Epic 9 ou NFR
- Screenshot / capture de la section erronée — V2

---

## 5. Project Structure Notes

```
apps/api/apps/professions/
  models.py                          ← ajout ProfessionReport (T1)
  migrations/
    0002_profession_report.py        ← T1
  serializers.py                     ← ajout ProfessionReportSerializer (T1)
  views.py                           ← ajout ProfessionReportCreateView + AdminListView (T1)
  urls.py                            ← nouvelles routes (T1)
  tests/
    test_reports.py                  ← T3 backend

apps/web/src/components/professions/
  ReportErrorButton.tsx              ← T2
  ReportErrorForm.tsx                ← T2
  __tests__/
    ReportErrorButton.test.tsx       ← T3 frontend

apps/web/src/hooks/
  useReportProfessionError.ts        ← T2
```

**Conventions à respecter :**
- RLS Story 1.8 sur tous les endpoints
- Audit log Story 1.13 sur création signalement
- Tokens CSS uniquement (Story 1.2)
- shadcn/ui : `Dialog`, `Select`, `Textarea`, `Button`, `Toast`

---

## 6. References

- **Epic 3 detail** : `_bmad-output/planning-artifacts/epics/epic-3-recommandation-vocationnelle-premier-aha.md` § Story 3.8
- **Story 3.12** : `FicheMetier` — intègre ce composant en pied de fiche
- **Story 3.2** : référentiel professions — fournit le modèle `Profession` (FK dans `ProfessionReport`)
- **Epic 9** : interface admin modération — traitement des signalements
- **Story 1.8** : RLS PostgreSQL
- **Story 1.13** : journal audit
- **PRD** : FR24 (signaler erreur fiche métier)

---

## 7. Dev Agent Record

### Agent Model Used
claude-sonnet-4-6

### Completion Notes List

- **T1**: `ProfessionReport` model avec `ErrorType` enum (4 valeurs), `Status` enum. Migration `0003`. Serializers séparés (create / response / admin). Vues `ProfessionReportCreateView` (IsStudent) et `ProfessionReportAdminListView` (IsPathAdmin). Audit log `profession_report_created`. Tests pytest en `test_reports.py` (11 tests, require PostgreSQL — marqués `@pytest.mark.postgresql_only`).
- **T2**: Hook `useReportProfessionError` (TanStack Query mutation, CSRF). `ReportErrorForm` avec Select shadcn obligatoire, Input localisation optionnel, Textarea 500 chars avec compteur, validation inline. `ReportErrorButton` avec toast stateful (4s, `aria-live="polite"`), état `reported` session-local, dialog desktop / sheet mobile (via `useIsMobile`). Intégré en pied de `FicheMetierMobile` et `FicheMetierDesktop` (absent de `FicheMetierPrint`).
- **T3**: 18 tests frontend (7 `ReportErrorButton` + 10 `ReportErrorForm` + 1 placeholder). FicheMetier tests wrappés avec `QueryClientProvider` (27/27 toujours verts). `scrollIntoView` shim ajouté à `test-setup.ts`.
- **Décision**: Tests ReportErrorButton mockent `ReportErrorForm` pour éviter les crashes jsdom du Select Radix. Les comportements du formulaire (validation, compteur) sont testés via `ReportErrorForm.test.tsx` en isolation.

### File List

- `apps/api/apps/professions/models.py` — ajout `ProfessionReport`
- `apps/api/apps/professions/migrations/0003_profession_report.py` — migration
- `apps/api/apps/professions/serializers.py` — ajout 3 serializers Report
- `apps/api/apps/professions/views.py` — ajout 2 vues Report
- `apps/api/apps/professions/urls.py` — 2 nouvelles routes report
- `apps/api/apps/professions/tests/test_reports.py` — 11 tests backend
- `apps/web/src/hooks/useReportProfessionError.ts` — hook mutation
- `apps/web/src/components/professions/ReportErrorForm.tsx` — formulaire
- `apps/web/src/components/professions/ReportErrorButton.tsx` — bouton + dialog/sheet
- `apps/web/src/components/professions/FicheMetier.tsx` — intégration pied de fiche
- `apps/web/src/components/professions/__tests__/ReportErrorButton.test.tsx` — 8 tests
- `apps/web/src/components/professions/__tests__/ReportErrorForm.test.tsx` — 10 tests
- `apps/web/src/components/professions/__tests__/FicheMetier.test.tsx` — ajout QueryClientProvider wrapper
- `apps/web/src/test-setup.ts` — shim `scrollIntoView`

### Change Log

- 2026-06-20 — Story 3.8 créée (Epic 3 launch). Indépendante du moteur de scoring, développable en parallèle.
- 2026-06-20 — Story 3.8 implémentée : backend ProfessionReport + endpoint + audit log ; frontend ReportErrorButton + ReportErrorForm + hook. 455/458 tests passent (3 pre-existing failures hors scope).
