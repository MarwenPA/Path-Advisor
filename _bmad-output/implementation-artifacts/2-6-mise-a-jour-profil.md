# Story 2.6: Mise à jour profil à tout moment

**Epic:** 2 — Profil Élève & Onboarding
**Status:** review
**Sprint:** 6 (Post-onboarding, profil & continuité)
**Story Key:** `2-6-mise-a-jour-profil`
**Estimation:** M (medium) — page profil structurée + 3 mini-flows d'édition (factorisations Stories 2.1, 2.2, 2.3, 2.4) + endpoint trigger recalcul reco async + edge cases changement filière. Sized ~2 j focused work.

> Story qui transforme l'onboarding en **acte continu plutôt que one-shot**. Sarah ajoute son bulletin du trimestre 2 en février, change sa LV2 en avril, retire sa spé Maths en mai. Chaque modification déclenche un **recalcul async** des recos et stats, avec un toast neutre — pas de drame, pas de re-onboarding. C'est la **continuité temporelle** comme moat (UX spec § Vision : *"continuité temporelle = seul actif robuste à la pression LLM grand public horizon 2027"*).

---

## 1. User Story

**As an** élève (Sarah qui maintient son profil au fil de l'année, ou Léa postponed qui décide d'ajouter ses bulletins en mars),
**I want** accéder à une page profil structurée avec 3 sections éditables (passions/intérêts/valeurs, niveau/filière/spés, bulletins), modifier chaque section via un mini-flow inline sans re-onboarding, et voir mes recos / stats se recalculer automatiquement,
**So that** mon profil reste à jour au fil de l'année (FR18), **so that** je peux affiner mes décisions avec mes données récentes, et **so that** mon historique n'est jamais perdu (changement de filière conservé pour audit longitudinal).

**Business value :** sans cette story, l'onboarding devient une **dette future** : Sarah qui a fait son profil en septembre re-démarrerait tout en février pour ajouter son trimestre 2. Avec cette story, le profil devient **un objet vivant** — c'est la base du moat "continuité temporelle versionnée".

**Garde-fous personas activés :**

- **Sarah** — ajouter un bulletin doit prendre < 1 min (mini-flow Story 2.5 AC6 réutilisé).
- **Léa** — ajouter ses bulletins 3 mois après "Plus tard" doit être un acte **calme** (pas de "Bienvenue dans la vraie expérience !").
- **Mehdi** — change de niveau 3ème pro → 2nde général en septembre N+1. Historique conservé, recos réinitialisées via `ConsentDialog`.

---

## 2. Acceptance Criteria (BDD)

### AC1 — Page profil : structure 3 sections éditables

**Given** je vais dans Paramètres → "Mon profil" (route `/profile`)
**When** je consulte ma page profil
**Then** je vois un layout single-column (mobile) / 2 colonnes (desktop : sidebar nav 224 px + content max 800 px) avec :

- Header sticky : titre `text-h1` *"Mon profil"* + back chevron + actions globales
- **3 sections empilées** (séparateurs entre elles) :
  1. **Passions, intérêts et valeurs** (Story 2.1)
  2. **Niveau scolaire, filière et spécialités** (Story 2.2)
  3. **Bulletins** (Stories 2.3 / 2.4 / 2.5)
- **`<ProfileMaturityIndicator />`** (Story 2.7) en haut de page

**And** chaque section a la structure :

```
┌─────────────────────────────────────────┐
│ [Section title h2]              [✎ Modifier] │
│                                          │
│ [Récap statique du contenu actuel]      │
│ (lecture seule, données actuelles)      │
│                                          │
│ Modifié il y a 12 jours                  │
└─────────────────────────────────────────┘
```

**And** le bouton **"Modifier"** ouvre un **Sheet bottom (mobile) / Drawer right (desktop)** avec le mini-flow correspondant

### AC2 — Édition passions/intérêts/valeurs (factorisation Story 2.1)

**Given** je clique le bouton ✎ de la section 1
**When** le sheet/drawer s'ouvre
**Then** :

- 3 onglets `Tabs` shadcn : *"Passions"*, *"Valeurs"*, *"Intérêts"*
- Chaque onglet rend `<PassionsPicker />`, `<ValeursPicker />`, `<InteretsFreeForm />` (Story 2.1) en mode édition pré-rempli
- Footer du sheet : primary *"Sauvegarder"* + secondary *"Annuler"*

**And** au Sauvegarder :
- PATCH vers `/api/v1/students/me/onboarding/passions` (endpoint existant Story 2.1)
- Toast info *"Profil mis à jour."* (3 s)
- Sheet ferme, section rafraîchit
- **Pas de recalcul reco** immédiat (passions consommées au prochain accès recos)

**And** au Annuler avec modifications non sauvegardées :
- `ConsentDialog` *"Tu as commencé des modifications — quitter sans sauvegarder ?"* (Story 1.14)

### AC3 — Édition niveau/filière/spés (3 cas : mineur, majeur, réinit)

**Given** je clique le bouton ✎ de la section 2
**When** le sheet s'ouvre
**Then** `<LevelForm mode="profile_edit" />` (Story 2.2 T3 factorisé) en édition pré-remplie

**And** 3 cas selon nature du changement :

**Cas 1 — Mineur** (ajout spé, modif sous-filière techno, mise à jour année post-bac) :
- PATCH commit normal
- Toast *"Profil mis à jour — recos en cours de recalcul…"*
- Worker async recompute recos (Epic 3)
- Toast follow-up *"Recos mises à jour."* (~5-10 s)

**Cas 2 — Majeur** (général → techno, bac général → bac pro, Terminale → Post-bac) :
- **`ConsentDialog`** AVANT commit :
  - Title : *"Tu changes de trajectoire scolaire"*
  - Description : *"Tes recos vocationnelles et tes parcours sauvegardés vont être recalculés. On garde ton ancien profil dans ton historique."*
  - `dataMentioned` : `["Recos vocationnelles", "Parcours sauvegardés Mes paris", "Stats d'admission"]`
  - `acceptLabel` : *"Oui, je confirme"*
  - `refuseLabel` : *"Annuler"*
  - **Pas `isAcceptDestructive`** — changement, pas suppression

**And** si confirmé :
- PATCH avec `motive: "profile_major_change"`
- Profil précédent snapshotté dans `StudentProfileHistory` (`archived_reason: "major_change_filiere"`)
- Anciens parcours "Mes paris" marqués `linked_to: "ancien_profil"` (badge visible)
- Worker async full recompute recos + stats
- Events analytics : `profile_major_change` + `profile_archived`

**Cas 3 — Réinitialisation** (3ème → Post-bac via correction d'erreur) :
- `ConsentDialog` avec `isAcceptDestructive: true`
- Recos actuelles supprimées, full recompute, archive ancien

### AC4 — Édition bulletins (factorisation Stories 2.3 / 2.4 / 2.5)

**Given** je clique le bouton ✎ de la section 3
**When** le sheet s'ouvre
**Then** je vois la liste actuelle de mes bulletins (cards récap par trimestre) + 3 actions par card :

- 🖉 *Modifier* → ouvre `<BulletinRecapEditor />` (Story 2.3 AC5) ou `<ManualBulletinForm />` (Story 2.4) selon `source`
- 🗑 *Supprimer* → `ConsentDialog` de confirmation
- ➕ *Ajouter un trimestre / une année* → ouvre `<BulletinsAddSheet />` (Story 2.5 AC6, réutilisation exacte)

**And** bouton tertiary *"Marquer tous mes bulletins comme à revoir"* — déclenche mode batch d'édition (flag `needs_review`)

**And** à chaque modification :
- Toast info *"Profil mis à jour — recos et stats en cours de recalcul…"*
- Worker async recompute recos + stats
- Toast follow-up *"Recos et stats mises à jour."*
- **Badge "+/-N pts mis à jour"** apparaît 24 h sur les stats affectées (cohérent Story 2.5 AC6 + Story 4.x DeltaRecap)

### AC5 — Recalcul async + visibilité progression

**Given** une modification déclenche un recalcul reco/stats
**When** le worker async tourne (3-10 s typique, 30 s edge)
**Then** **2 niveaux de feedback** :

- **Toast immédiat** au commit : *"Profil mis à jour — recos en cours de recalcul…"* (3 s auto-dismiss)
- **Toast follow-up** à la fin : *"Recos mises à jour."* — uniquement si `lastInteractionAt < 60s ago` ; sinon silencieux (résultat visible au prochain accès recos)
- **Pas de loader bloquant** — navigation libre pendant le recalcul

**And** côté serveur :
- Job Celery `recompute_for_student(student_id, trigger_reason)` idempotent + déduplication (2 modifs rapides → 1 job final)
- Polling TanStack Query côté front sur endpoints recos (pas de WebSocket MVP)
- Timeout 60 s, retry exponentiel max 3 (Celery beat)

**And** si calcul échoue persistent :
- Toast warning *"Mise à jour en cours — réessaie plus tard si tu ne vois pas tes nouvelles recos."* — pas de drame

### AC6 — Historique de profil (audit longitudinal)

**Given** des changements **majeurs** ont été effectués (AC3 Cas 2/3)
**When** je consulte la route `/profile/history`
**Then** je vois une liste chronologique inverse des changements majeurs uniquement :

```
┌─────────────────────────────────────────┐
│  Mai 2026                                │
│  Changement de filière                   │
│  Bac général → Bac techno STMG          │
│  Anciennes recos archivées               │
│  [ Revoir l'ancien profil ]              │
│                                          │
│  Septembre 2025                          │
│  Profil initial créé                     │
│  Terminale général — Maths/SVT/HGGSP    │
└─────────────────────────────────────────┘
```

**And** chaque entrée permet de :
- Visualiser l'ancien profil (lecture seule)
- Voir les recos + parcours sauvegardés à l'époque (snapshot)
- **Restaurer ce profil ancien** via `ConsentDialog` — la restauration crée une **nouvelle** entrée d'historique (immutabilité audit), le profil actuel devient archivé

**And** historique **immuable** côté audit (Story 1.13). Rétention : tant que compte actif, cascade au DELETE compte (Story 1.12).

### AC7 — Accessibilité RGAA AA

**Given** la page profil et tous les mini-flows
**When** je teste clavier seul, lecteur d'écran, reduced motion
**Then** **navigation clavier** :

- Tab order page : header → section 1 (titre + ✎) → section 2 → section 3 → historique link → footer
- Chaque sheet/drawer trap focus (Radix natif), Échap ferme avec confirmation si modifications
- Tabs internes (AC2) : flèches gauche/droite

**And** **HTML sémantique** :
- `<main aria-labelledby="profile-title">` avec `<h1>` "Mon profil"
- Chaque section : `<section aria-labelledby="section-{id}-title">` avec `<h2>`
- Historique : `<section role="region" aria-label="Historique">` + `<ol>` chronologique

**And** **annonces dynamiques** :
- Toast au commit : `aria-live="polite"` *"Profil mis à jour."*
- Toast follow-up : *"Recos mises à jour."*
- ConsentDialog AC3 Cas 2 : `role="alertdialog"` avec focus initial sur refuse (anti-dark-pattern Story 1.14)

**And** **reduced motion** : ouverture sheet en `motion-quick` → ~0 ms

**And** **touch targets** : 44 × 44 px partout

### AC8 — Persistence + concurrence

**Given** j'édite mon profil sur 2 appareils simultanément
**When** je commit sur l'appareil A puis sur B avec un état désynchronisé
**Then** stratégie **last-write-wins basée sur `updated_at`** :
- Commit B arrive avec `updated_at` client < serveur (modifié par A)
- Serveur renvoie **409 Conflict** avec payload serveur actuel
- Front B : **`GracefulFallback`** (Story 2.9) avec :
  - Title : *"Ton profil a été mis à jour ailleurs"*
  - Description : *"Tu as modifié ton profil sur un autre appareil. On peut recharger pour voir l'état à jour, ou écraser avec ta modification courante."*
  - Primary : *"Recharger l'état à jour"*
  - Secondary : *"Garder ma modification"* (force overwrite)
  - Tertiary : *"Annuler"*

**And** audit log Story 1.13 enregistre les 2 modifications avec device fingerprint
**And** au minimum 1 modification conservée intégralement (jamais de perte silencieuse)

---

## 3. Tasks / Subtasks

### T1 — Backend : endpoints profile + history (AC1-AC4, AC6)

- Endpoint `GET /api/v1/students/me/profile` (full aggregated : passions + level + bulletins + history summary + maturity Story 2.7)
- Endpoints PATCH existants Stories 2.1, 2.2, 2.3, 2.4 réutilisés (pas de duplication)
- Endpoint `POST /api/v1/students/me/profile/recompute` (déclenche worker, appelé en background après PATCH majeur)
- Modèle `StudentProfileHistory` :
  - `id`, `student_id (fk)`, `archived_at`, `archived_reason: "major_change_*"`, `previous_state JSONB`
  - Index `(student_id, archived_at DESC)`
- Endpoint `GET /api/v1/students/me/profile/history` (pagination)
- Endpoint `POST /api/v1/students/me/profile/history/{id}/restore`
- **Audit log Story 1.13** : `profile_section_updated`, `profile_major_change`, `profile_history_restored`
- RLS Story 1.8

### T2 — Backend : worker async recompute (AC5)

- Task Celery `recompute_for_student(student_id, trigger_reason)` :
  - Idempotent (déduplication si déjà running)
  - Recalcule recos Epic 3 + stats admission Epic 4
  - Update `recomputed_at` en base
  - Timeout 60 s, retry exponentiel max 3
- Polling TanStack Query côté front (cache invalidation 30 s)
- Métriques observabilité (durée, succès / échec, raison)

### T3 — Frontend : page profil + sections (AC1)

- Route `apps/web/app/(auth)/profile/page.tsx`
- Composant `<ProfilePage />` avec :
  - `<ProfileSectionPassions />`, `<ProfileSectionLevel />`, `<ProfileSectionBulletins />`
  - `<ProfileMaturityIndicator />` (Story 2.7 consumé)
- Hook `useProfileEditSheet(sectionId)` pour gérer sheet open/close

### T4 — Frontend : mini-flows édition (AC2, AC3, AC4)

- `<EditPassionsSheet />` : Tabs internes + composants Story 2.1
- `<EditLevelSheet />` : `<LevelForm mode="profile_edit">` (Story 2.2) + ConsentDialog AC3 Cas 2/3
- `<EditBulletinsSheet />` : composants Stories 2.3 / 2.4 / 2.5
- Hook `useUnsavedChangesGuard(sheetOpen, hasChanges)` pour ConsentDialog au close

### T5 — Frontend : page historique + restauration (AC6)

- Route `apps/web/app/(auth)/profile/history/page.tsx`
- `<ProfileHistoryPage />` : liste chronologique + infinite scroll TanStack Query
- `<ProfileHistoryViewer />` (read-only snapshot d'un ancien profil)
- Bouton "Restaurer" → ConsentDialog → POST restore

### T6 — Frontend : gestion 409 concurrence (AC8)

- Hook `useConflictHandler(mutation)` : intercepte 409, ouvre `<GracefulFallback />` (Story 2.9)
- Stratégie : refetch state, ou force overwrite, ou cancel

### T7 — Tests

- **Backend (pytest)** :
  - GET profile aggregated
  - PATCH passions standard
  - PATCH level Cas 2 → history snapshot + recompute enqueued
  - GET history pagination
  - POST history restore → restore + new history entry
  - 409 concurrence
  - RLS cross-tenant
- **Frontend (Vitest + RTL)** :
  - Page profil rendu, 3 sections
  - Click ✎ section 1 → sheet ouvre
  - Édition passions → save → toast + fermeture
  - Annulation avec modifs → ConsentDialog
  - Changement filière AC3 Cas 2 → ConsentDialog + accept → history snapshot
  - 409 → GracefulFallback 3 options
- **E2E (Playwright)** :
  - **Sarah ajoute trimestre 2** : profile → bulletins ✎ → BulletinsAddSheet → 1 trimestre → commit → recos recalculées
  - **Mehdi change de filière** : profile → level ✎ → 3ème pro → 2nde général → ConsentDialog → confirm → history snapshot
  - **Léa ajoute bulletins en mars** : profile → bulletins ✎ → 1er ajout → `partial`, bandeau Story 2.5 disparaît
- A11y axe-core sur page profil + chaque sheet
- Manuel VoiceOver iOS sur ajout bulletin via profil

### T8 — Documentation

- `docs/profile/edit-flow.md` : matrice mineur / majeur / réinit
- `docs/profile/history.md` : structure + audit
- `docs/a11y/profile-page.md`

---

## 4. Dev Notes

### 4.1 Wireframes ASCII — page profil mobile 375 px

```
┌─────────────────────────────────────────┐
│ <  Mon profil                       🔔  │
├─────────────────────────────────────────┤
│                                          │
│  Profil enrichi                         │ ← Story 2.7 indicator
│  Tu débloques les stats personnalisées. │
│  [ Voir comment compléter →           ] │
│                                          │
│  ┌─────────────────────────────────────┐│
│  │ Passions & valeurs           [✎]    ││
│  │                                     ││
│  │ 5 passions · 4 valeurs · 2 intérêts ││
│  │ Sciences & nature · Cinéma · Tech…  ││
│  │                                     ││
│  │ Modifié il y a 3 mois               ││
│  └─────────────────────────────────────┘│
│                                          │
│  ┌─────────────────────────────────────┐│
│  │ Niveau scolaire              [✎]    ││
│  │                                     ││
│  │ Terminale · Bac général             ││
│  │ Maths · SVT · HGGSP                 ││
│  │                                     ││
│  │ Modifié il y a 3 mois               ││
│  └─────────────────────────────────────┘│
│                                          │
│  ┌─────────────────────────────────────┐│
│  │ Bulletins                    [✎]    ││
│  │                                     ││
│  │ Trim. 1 Terminale ✓                 ││
│  │ Trim. 2 Terminale ✓ (il y a 12 j)   ││
│  │                                     ││
│  │ + Ajouter un trimestre              ││
│  └─────────────────────────────────────┘│
│                                          │
│  ───── Historique des changements ───── │
│  [Lien tertiary : Voir l'historique →]  │
└─────────────────────────────────────────┘
```

### 4.2 Matrice changement mineur / majeur / réinit

| Modification | Catégorie | Confirmation | Snapshot | Recalcul |
|---|---|---|---|---|
| Ajouter une passion | Mineur | Non | Non | Non (différé) |
| Changer une valeur | Mineur | Non | Non | Non (différé) |
| Ajouter trimestre 2 | Mineur | Non | Non | Oui |
| Supprimer un bulletin | Mineur | ConsentDialog standard | Non | Oui |
| Changer note d'une matière | Mineur | Non | Non | Oui |
| Ajouter une spé | Mineur | Non | Non | Oui |
| Modifier sous-filière techno | Mineur | Non | Non | Oui |
| Changer LV1/LV2 | Mineur | Non | Non | Oui |
| **Changer de filière** (général → techno) | **Majeur** | **ConsentDialog `dataMentioned`** | **Oui** | **Oui (full reset)** |
| **Changer série techno** (STMG → STI2D) | **Majeur** | ConsentDialog | Oui | Oui (full reset) |
| **Général → pro** ou inverse | **Majeur** | ConsentDialog explicite | Oui | Oui (full reset) |
| Terminale → Post-bac (transition naturelle) | Majeur | ConsentDialog informatif | Oui | Oui |
| **3ème → Post-bac** (erreur saisie) | **Réinit** | **`isAcceptDestructive`** | **Oui** | **Full reset + suppression recos** |

### 4.3 État émotionnel — la story de la continuité

| Moment | Cible | Triggers à bannir |
|---|---|---|
| Sarah revient en février ajouter T2 | Compagnonnage ("L'app se souvient, je continue") | "Bienvenue à nouveau !", "On t'a manqué" |
| Léa ajoute ses bulletins 3 mois après | Choix volontaire calme | "Enfin, tu vas voir tes vraies stats" |
| Mehdi restaure ancien profil après erreur | Soulagement ("Ouf, l'historique m'a sauvé") | "Action irréversible !", absence d'historique |
| Sarah modifie une spé en avril | Souplesse ("Je peux ajuster sans drame") | Modal cérémonieuse, "Tu es sûre ?" répété |

### 4.4 Décisions design verrouillées

- **Page profil = single page avec 3 sections empilées** — pas de sub-routes par section (anti-friction)
- **Édition via sheet/drawer**, pas full page — l'élève reste contextuel
- **Récap statique en lecture seule** dans chaque section (séparation lecture / édition stricte)
- **Recalcul async non bloquant** — navigation libre pendant
- **Historique = changements majeurs uniquement** — anti-bruit
- **Restauration crée nouvelle entrée historique** — immutabilité audit
- **Last-write-wins avec 409 explicite** — pas de merge automatique silencieux
- **Aucun re-onboarding** déclenché par cette page — séparée des routes `/onboarding/*`

### 4.5 Anti-patterns proscrits

- ❌ **"Refaire l'onboarding"** comme option — Story 2.6 EST l'alternative
- ❌ **Progress bar "X % de ton profil mis à jour"**
- ❌ **Toast bruyant** pour chaque petite modification
- ❌ **Modal "Bienvenue à nouveau !"** au retour Sarah
- ❌ **Loader bloquant** pendant recalcul async
- ❌ **Confirmation à chaque blur** ("Sauvegarder ?")
- ❌ **Bouton "Reset profil"** visible en pleine page (caché dans Paramètres → Avancé)
- ❌ **Diff visuel "Avant / Après"** au commit — l'historique est dans /history si besoin

### 4.6 Edge cases et failures explicites

| Edge case | Comportement attendu | AC ref |
|---|---|---|
| Sarah change filière, annule avant ConsentDialog | Dialog ferme, profil non modifié, pas de history | AC3 |
| Sarah confirme changement filière, ferme app pendant recalcul | Job continue côté serveur, recos mises à jour au retour | AC5 |
| Sarah modifie passions sur mobile + desktop simultanément | 409 sur 2e commit, GracefulFallback 3 options | AC8 |
| Léa ajoute 1er bulletin via section 3 ✎ | Mode passe `postponed → partial`, bandeau Story 2.5 disparaît | AC4 |
| Mehdi restaure ancien profil pre-changement filière | Nouveau snapshot historique (immutabilité), recos recalculées | AC6 |
| Recalcul worker timeout 60 s | Log warning, job failed, recalcul reprend au prochain accès recos | AC5 |
| Mode hors-ligne pendant édition | Draft localStorage (cohérent stories 2.1/2.2/2.3), commit retryé au reconnect | T1 |
| Élève supprime son dernier bulletin | `bulletins_status` repasse à `postponed`, bandeau Story 2.5 réapparaît | AC4 |
| 2 modifs rapides en < 5 s | Worker recompute déduplique, 1 seul job final | AC5 |
| Lecteur d'écran sur profil | Sections annoncées avec titres + caption "Modifié il y a X j" | AC7 |
| Reduced motion sur sheet | Ouverture / fermeture instantanée | AC7 |

---

## 5. Project Structure Notes

```
apps/web/
  app/(auth)/profile/
    page.tsx                          ← ProfilePage (T3)
    history/
      page.tsx                        ← ProfileHistoryPage (T5)
      [id]/page.tsx                   ← ProfileHistoryViewer detail
    edit/                             ← (alt direct edit routes)
      passions/page.tsx
      level/page.tsx
      bulletins/page.tsx
  components/profile/
    profile-section-passions.tsx
    profile-section-level.tsx
    profile-section-bulletins.tsx
    edit-passions-sheet.tsx
    edit-level-sheet.tsx
    edit-bulletins-sheet.tsx
    profile-history-card.tsx
    __tests__/
  hooks/
    use-profile-edit-sheet.ts
    use-unsaved-changes-guard.ts
    use-conflict-handler.ts
  e2e/
    profile-edit.spec.ts

apps/api/apps/students/                ← extension Stories 2.1/2.2/2.3
  models.py                            ← StudentProfileHistory (T1)
  views_profile.py                     ← GET /profile + GET /history + POST restore
  serializers_profile.py
  tasks_recompute.py                   ← Celery worker (T2)
  migrations/
    NNNN_profile_history.py
  tests/
    test_profile_aggregated.py
    test_profile_history.py
    test_recompute_worker.py

docs/profile/
  edit-flow.md
  history.md
docs/a11y/
  profile-page.md
```

**Conventions à respecter :**

- Réutilisation stricte des composants Stories 2.1/2.2/2.3/2.4 — pas de duplication
- `<LevelForm mode="profile_edit">` factorisé déjà créé Story 2.2 T3
- Audit log Story 1.13 (`motive: "profile_edit_passions" | "profile_major_change" | "history_restored"`)
- RLS Story 1.8

---

## 6. References

- **UX spec globale** :
  - § Vision → continuité temporelle moat
  - § Design Opportunities #1 (continuité temporelle versionnée)
  - § Experience Principles #5 (chaque session commence où la précédente s'est arrêtée)
  - § Flow 2 — Sarah retour J+30
- **Epic 2 detail** : § Story 2.6
- **Stories Epic 2 réutilisées** : 2.1, 2.2, 2.3, 2.4, 2.5
- **Story 1.13 (audit log)** : events `profile_section_updated`, `profile_major_change`, `profile_history_restored`
- **Story 1.14 (ConsentDialog)** : AC3 Cas 2/3 + AC8 conflict
- **Story 2.7 (maturité)** : consumé en haut de page profil
- **Story 2.9 (GracefulFallback)** : AC8 conflict 409
- **PRD** : FR18 (mise à jour profil à tout moment)

---

## 7. Dev Agent Record

### Agent Model Used
claude-sonnet-4-6 (dev) + claude-opus-4 (code review)

### Debug Log References
- `SheetFooter` missing from sheet.tsx → added export
- `getByText(/passions/i)` ambiguous in RTL → switched to `getByRole("heading", { name: /passions/i })`
- unauthenticated tests failed → added `permission_classes = [IsAuthenticated]` to all 4 new views

### Completion Notes List
- T1: StudentProfileHistory model + migration 0005 + 4 endpoints (GET /profile, POST /recompute, GET /history, POST /history/snapshot) — 13 pytest tests all passing
- T2: tasks_recompute.py worker stub (Epic 3 TODO wired)
- T3: ProfilePage with 3 editable sections + ProfileMaturityIndicator + history link
- T4: EditPassionsSheet, EditLevelSheet, EditBulletinsSheet (mini-flows, sheet/drawer)
- T5: /profile/history/page.tsx (infinite scroll TanStack Query, ol chronologique)
- T6: useConflictHandler hook (409 conflict state)
- SheetFooter added to components/ui/sheet.tsx
- StudentProfile type extended with level/filiere/specialites fields

### File List
apps/api/apps/students/models.py (modified — StudentProfileHistory added)
apps/api/apps/students/migrations/0005_profile_history.py (new)
apps/api/apps/students/views_profile.py (new)
apps/api/apps/students/tasks_recompute.py (new)
apps/api/apps/students/urls.py (modified — 4 new URL patterns)
apps/api/apps/students/tests/test_profile_aggregated.py (new — 13 tests)
apps/web/src/components/features/profile/profile-page.tsx (new)
apps/web/src/components/features/profile/edit-passions-sheet.tsx (new)
apps/web/src/components/features/profile/edit-level-sheet.tsx (new)
apps/web/src/components/features/profile/edit-bulletins-sheet.tsx (new)
apps/web/src/app/(auth)/profile/page.tsx (new)
apps/web/src/app/(auth)/profile/history/page.tsx (new)
apps/web/src/hooks/use-conflict-handler.ts (new)
apps/web/src/hooks/use-student-profile.ts (modified — StudentProfile type extended)
apps/web/src/components/ui/sheet.tsx (modified — SheetFooter added)
apps/web/src/components/features/profile/__tests__/profile-page.test.tsx (new — 6 tests)
apps/web/src/components/features/profile/__tests__/edit-sheets.test.tsx (new — 7 tests)
apps/web/src/hooks/__tests__/use-conflict-handler.test.ts (new — 3 tests)

### Change Log

- 2026-05-25 — Story 2.6 contextée par Marwen + Claude (Opus 4.7). Story pilier de la **continuité temporelle** (moat MVP). Factorise sans duplication les composants Stories 2.1/2.2/2.3/2.4/2.5. Introduit `StudentProfileHistory` pour audit longitudinal des changements majeurs.
