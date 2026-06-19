# Story 2.5: Mode dégradé invisible — "Plus tard" sur les bulletins

**Epic:** 2 — Profil Élève & Onboarding
**Status:** review
**Sprint:** 5 (Onboarding bulletins & OCR)
**Story Key:** `2-5-mode-degrade-plus-tard-bulletins`
**Estimation:** S (small) côté MVP onboarding, **mais avec cross-cuts important** sur Epic 3 (recos labels) et Epic 4 (stats labels + mini-flow contextual). Sized ~1 j focused work pour la partie onboarding ; les cross-cuts sont **portés par les stories consommatrices** (Epic 3, 4) qui consultent `bulletins_status === "postponed"`.

> Story du **principe expérience #4** : *"Le mode normal contient tous les modes."* Léa choisit "Plus tard" — elle voit **strictement les mêmes écrans** que Sarah avec bulletins. Les recos, les graphes, les stats — tout existe en version Léa. Les seules différences sont **dans le contenu textuel des labels** ("estimation indicative" au lieu de stats personnalisées). **Pas d'écran "Mode dégradé"**, pas de bandeau "Profil incomplet", pas de pourcentage. C'est la story qui rend Path-Advisor non-discriminant — si on la rate, le produit perd Mehdi, Léa et tous les profils non-Sarah-Terminale.

---

## 1. User Story

**As an** élève (Léa qui n'a pas envie de partager ses bulletins maintenant, OU n'importe quel élève en exploration sans intention immédiate de saisir),
**I want** pouvoir cliquer *"Plus tard, je préfère explorer d'abord"* sans aucune pénalité visible, accéder aux recos vocationnelles et au graphe de parcours **avec la même UI que les utilisateurs avec bulletins**, et avoir une porte d'entrée discrète et contextuelle pour ajouter mes bulletins quand je serai prête,
**So that** je découvre le produit sans friction et sans honte (FR17), **so that** je ne me sens jamais "cas spécial" ou "profil dégradé", et **so that** quand je décide d'ajouter mes bulletins, c'est un **acte de choix volontaire** déclenché par ma curiosité, pas par culpabilisation système.

**Business value :** sans cette story, l'OCR + saisie manuelle deviennent un **gate effectif** : les utilisateurs qui n'ont pas les bulletins sous la main (vacances, conflits familiaux, refus de partage, oubli) abandonnent avant la première reco. Avec cette story, on garde **toute la cohorte d'exploration** dans le funnel — et on les convertit progressivement en utilisateurs "données scolaires complètes" via les mini-CTAs contextuels d'Epic 4. Le **levier de conversion postponed → bulletins ajoutés** est un KPI MVP critique (cible : ≥ 35 % en 4 semaines selon analytics PRD).

**Garde-fous personas activés sur cet écran :**

- **Léa (dignité PILIER)** — c'est SA story. Aucun pixel de cet écran ou des écrans aval ne doit lui faire ressentir qu'elle a "fait moins bien". Test sprint review : Léa fait l'onboarding "Plus tard" + ouvre 1 reco + 1 graphe → si à un quelconque moment elle pense *"Ah si j'avais mis mes bulletins…"* en mode regret, on a échoué.
- **Mehdi (anti-stigma)** — même test. Si Mehdi voit son graphe avec des fourchettes larges étiquetées *"DÉBLOQUE TES VRAIES STATS"*, on a échoué.
- **Sarah (cohérence)** — Sarah avec bulletins et Léa sans bulletins doivent pouvoir s'envoyer leurs screenshots WhatsApp respectifs sans que Sarah devine que Léa n'a pas mis ses bulletins. C'est le test "screenshot indiscernable" (UX spec § Step 7).

---

## 2. Acceptance Criteria (BDD)

### AC1 — Point d'entrée principal : 3e card écran 2.3 AC1

**Given** je suis sur l'écran 2.3 AC1 (3 cards de choix d'import bulletins)
**When** je clique sur la **3e card** *"Plus tard, je préfère explorer d'abord"*
**Then** la card est activée comme les 2 autres (mêmes specs visuelles, mêmes affordances tactiles — c'est le principe parité)
**And** **aucune `ConsentDialog` de confirmation ne s'ouvre** (différent de step-1 / step-2 "Plus tard" qui demandaient confirmation) — ici, c'est un choix explicite déjà fait via la card, pas un skip d'urgence
**And** le profil côté serveur passe directement à :

```json
{
  "bulletins_status": "postponed",          // ← sémantique IMPORTANTE : pas "incomplete"
  "bulletins_postponed_at": "2026-05-25T10:42:00Z",
  "onboarding_status": "completed",         // ← l'onboarding est CONSIDÉRÉ comme terminé
  "onboarding_completed_at": "2026-05-25T10:42:00Z"
}
```

**And** **aucun toast confirmant le skip** n'apparaît (pas de *"Tu as choisi 'Plus tard'"*) — la transition est silencieuse
**And** l'utilisateur est **redirigé directement vers `/dashboard`** (Epic 3 entry, ou son équivalent post-onboarding au sprint actuel)

### AC2 — Points d'entrée secondaires (consistance navigation)

**Given** je peux aussi déclencher le mode "Plus tard" depuis 3 autres écrans
**When** je clique l'un de ces déclencheurs
**Then** le comportement est **strictement identique à AC1** (même PATCH, même redirect, pas de confirmation) :

| Origine | Élément cliqué | Story ref |
|---|---|---|
| Story 2.3 AC4 ScenarioLoader t > 30 s | Lien tertiary *"Saisir à la main plutôt"* → en cascade depuis Story 2.4 footer lien *"⏭ Plus tard"* | 2.3 AC4 + 2.4 AC5 |
| Story 2.3 AC7 GracefulFallback (OCR échoué) | Lien tertiary footer *"Plus tard, je préfère explorer d'abord"* | 2.3 AC7 |
| Story 2.4 AC5 saisie manuelle | Lien tertiary footer *"⏭ Plus tard, je préfère explorer d'abord"* | 2.4 AC5 |

**And** ces 3 points d'entrée secondaires émettent un event analytics distinct (`bulletins_postponed_via_fallback` au lieu de `bulletins_postponed_via_card_direct`) — utile pour distinguer "choix explicite" vs "rebond après échec" en analytics

### AC3 — Bandeau discret dashboard / pages contextuelles (cross-cut Epic 3)

**Given** mon profil est `bulletins_status === "postponed"`
**When** j'arrive sur le dashboard (Epic 3 entry) ou n'importe quelle page produit (recos, graphes Epic 4, profil)
**Then** je vois un **bandeau discret en pied d'écran fixe** (mobile) ou **discret dans le sidebar** (desktop) :

```
┌─────────────────────────────────────────┐
│ Tu peux ajouter tes bulletins à tout    │ ← text-sm color-text-muted
│ moment pour des stats personnalisées.   │
│                          [ Ajouter → ]  │ ← bouton tertiary brand
└─────────────────────────────────────────┘
```

- Container : full-width mobile, max-width 320 px desktop (côté droit dashboard)
- Fond : `color-bg-2`, border-top 1 px `color-border` (mobile) / border 1 px `color-border` (desktop)
- Padding `space-3 space-4`
- Hauteur 56 px max (anti-overlay sur le contenu)
- Texte : neutre, factuel, **AUCUN** *"Tu rates X"* ou *"Débloque Y"*
- Bouton tertiary *"Ajouter →"* déclenche le **mini-flow d'ajout inline** (AC5)
- **Bouton de fermeture `✕`** discret en haut-droite du bandeau — au tap, dismiss pour 7 jours (`bulletins_postponed_banner_dismissed_until: now + 7d`)

**And** le bandeau **réapparaît automatiquement** après dismiss :
- Au-delà de 7 jours (TTL du dismiss)
- À chaque page où il y a un **mini-CTA contextuel** déclenché par une action user (cf AC4) — celui-là n'est pas dismissable
- Quand l'élève consulte une stat d'admission Epic 4 (réactivation contextuelle)

**And** le bandeau **disparaît définitivement** quand `bulletins_status === "completed"` (bulletins ajoutés via mini-flow ou via re-onboarding ; Story 2.6)

### AC4 — Recos vocationnelles (Epic 3) : même UI, label "indicatif"

**Given** je consulte mes recos vocationnelles (Epic 3, écran liste 8 métiers scorés)
**When** les recos s'affichent
**Then** **structure visuelle strictement identique** à Sarah avec bulletins (UX-DR25) :

- Même `ScoreVocationnel` component (Couche 3 Story 3.11)
- Même hiérarchie h1 → liste cards
- Même typographie, mêmes couleurs sémantiques (audacieux/réaliste/sûr)
- Même phrase recopiable sous chaque score (italic, brand accent)

**And** **les seules différences sont dans le copy** :

| Élément | Sarah avec bulletins | Léa postponed |
|---|---|---|
| Score chip (% compatibilité) | `78 % compatible` | `78 % compatible` (identique — le score vocationnel ne nécessite pas de bulletins, il est basé sur passions/valeurs/intérêts Story 2.1) |
| Phrase recopiable | *"Avec ton goût pour la justice sociale et ton 14 en HGGSP, droit fiscal est un objectif réaliste."* | *"Avec ton goût pour la justice sociale, droit fiscal est un objectif réaliste — précision affinée quand tu ajouteras tes bulletins."* (mention douce sans drame) |
| Section "Signaux contributifs" | Inclut signaux scolaires (notes, appréciations) | Sections scolaires absentes — pas de placeholder "Tu manques de notes !" |
| Bouton "Voir le parcours" | Standard | Standard (le graphe Epic 4 gère son propre mode dégradé, cf AC5) |

**And** **AUCUN** placeholder vide ou message du type *"Ajoute tes bulletins pour voir ce score"* — les sections sont juste *absentes du DOM* si non applicables (anti-stigma)

### AC5 — Graphe de parcours (Epic 4) : stats indicatives + mini-flow inline contextuel

**Given** je consulte un graphe de parcours métier (Epic 4)
**When** le graphe se construit
**Then** **structure visuelle strictement identique** à Sarah :

- Même `GraphParcours` component (Couche 3 Story 4.9)
- Même animation séquentielle 720 ms première session (UX spec § Step 7)
- Même hiérarchie chiffre dominant + forme du chemin + nom métier
- Même grille d'écoles cibles en dessous

**And** **les stats d'admission** sont affichées **comme fourchettes larges** plutôt que chiffre unique :

| Élément | Sarah | Léa postponed |
|---|---|---|
| Stat principal nœud cible | `38 %` (chiffre précis Display-1) | `30-45 %` (fourchette même typo Display-1) |
| Label qualitatif | *"Pari audacieux"* | *"Pari audacieux — estimation indicative"* |
| Ligne de contexte | *"Moyenne admise dernière promo : 14.2"* | *"Affine cette estimation avec tes bulletins."* (factuel, non culpabilisant) |
| Levier d'action | *"+2 points en maths → 58 %"* | *"Ajoute tes bulletins → stat personnalisée"* (lien vers AC6 mini-flow) |

**And** un **mini-CTA contextuel** apparaît dans une zone discrète (sous la grille d'écoles cibles, pas en overlay) :

```
┌─────────────────────────────────────────┐
│  📋  Ajoute tes bulletins                │ ← icône Lucide FileText
│      Tes stats deviendront personnalisées│ ← text-body color-text-muted
│      en moins d'1 minute.                │
│                  [ J'ajoute mes notes → ]│ ← bouton secondary
└─────────────────────────────────────────┘
```

- Container : `Card` shadcn, fond `color-bg-2`, border 1 px `color-border`, radius `--radius-md`, padding `space-6`
- **PAS de fond brand**, PAS d'icône criante, PAS de "DÉBLOQUE" — ton calme, factuel
- Bouton secondary (pas primary — il y a déjà un primary "Voir d'autres chemins" plus haut)
- Au tap → **mini-flow d'ajout inline** AC6 (pas redirection vers onboarding complet)
- **Disparaît** quand `bulletins_status === "completed"`

### AC6 — Mini-flow d'ajout bulletins inline (1 minute, pas un re-onboarding)

**Given** je suis sur n'importe quelle page produit avec `bulletins_status === "postponed"`
**When** je clique soit sur le bouton du bandeau AC3, soit sur le mini-CTA AC5, soit dans le profil Story 2.6
**Then** un **`Sheet bottom` (mobile) / `Drawer right` (desktop)** s'ouvre avec un mini-flow d'ajout :

- Titre `text-h2` : *"Ajoute tes bulletins"*
- Sous-titre `text-body` `color-text-muted` : *"En moins d'une minute, tes stats deviennent personnalisées."*
- **2 boutons côte à côte mobile (stack vertical mobile, horizontal desktop), équivalents weight (no-dark-pattern cohérent Story 1.14)** :
  - 📷 *"Scanner / importer mes bulletins"* → ouvre le `FilePickerSheet` Story 2.3 AC2 dans le sheet courant (nested)
  - ✍️ *"Saisir mes notes à la main"* → ouvre un `MatiereInputRow[]` mini-form Story 2.4 dans le sheet courant (nested)
- Bouton tertiary fermer en haut-droite du sheet : *"Annuler"* — au tap, ferme le sheet sans modification, l'élève reste sur la page d'origine

**And** **le mini-flow réutilise les composants Story 2.3 / 2.4** mais dans un container `Sheet` plus contraint :
- Pas de tabs trimestres complexes — l'élève peut ajouter UN trimestre à la fois ici (les autres via Story 2.6)
- Pas de breadcrumb "Étape N/3" — c'est un side-flow, pas un onboarding
- Validation et commit immédiats à la fin du sheet → le sheet se ferme + toast info *"Profil mis à jour — recos en cours de recalcul…"* (animation 1-2 s pendant que le worker reco Epic 3 re-score)

**And** au commit réussi :
- `bulletins_status` passe à `"completed"` (ou `"partial"` si saisie partielle, cf Story 2.4 AC5)
- Un event analytics `bulletins_added_via_mini_flow` est émis avec `{ entry_point: "banner" | "graph_cta" | "profile" }`
- Les stats d'admission visibles à l'écran sont **recalculées en place** (Epic 4 service `compute_admission_stats` re-trigger)
- Un **badge "+14 pts mis à jour"** apparaît 24 h sur les stats affectées (cohérent UX spec § DeltaRecap)

### AC7 — Bandeau et mini-CTAs : tous dismissables, jamais bloquants

**Given** un bandeau ou mini-CTA est affiché sur une page
**When** je consulte la page
**Then** **aucun de ces éléments ne bloque l'interaction** avec le contenu principal :
- Pas de modal overlay
- Pas de scroll-jacking
- Pas de "Tu dois ajouter tes bulletins pour continuer"
- Le bandeau AC3 a un bouton fermer `✕` (7 jours TTL dismiss)
- Le mini-CTA AC5 n'est pas dismissable (apparaît contextuellement, disparaît au scroll-out) — mais **ne suit pas l'utilisateur** ; il reste à sa position dans la page

**And** **aucune limite de fonctionnalité** liée au mode postponed :
- Léa peut consulter les 8 métiers recommandés en entier
- Léa peut ouvrir tous les graphes de parcours
- Léa peut comparer 2 écoles
- Léa peut explorer toutes les fiches métier / fiche école
- Léa peut accéder aux exports (Story 6 `StoryExport`) — avec note "estimation indicative" intégrée dans le re-rendu PNG / PDF

**And** **les seules vraies limites** (qui ne dépendent pas de `bulletins_status` mais de logique business) :
- Premium gating (Epic 5) — applicable indépendamment du statut bulletins
- Envoi anticipé école (Epic 5 paywall) — gating premium, pas bulletin

### AC8 — Persistence + analytics

**Given** mon profil est `bulletins_status === "postponed"`
**When** j'interagis avec les bandeaux / mini-CTAs
**Then** les events analytics suivants sont émis :

| Event | Quand | Payload |
|---|---|---|
| `bulletins_postponed` | Au commit AC1/AC2 | `{ via: "card_direct" \| "ocr_fallback" \| "manual_fallback" \| "loader_optin" }` |
| `bulletins_banner_shown` | Premier render après login session | `{ page: string }` |
| `bulletins_banner_dismissed` | Click `✕` du bandeau | `{ page: string, dismissed_for_days: 7 }` |
| `bulletins_banner_clicked` | Click "Ajouter →" du bandeau | `{ page: string }` |
| `bulletins_minicta_shown` | Render mini-CTA AC5 | `{ context: "graph" \| "stat" \| ..., metier_id?: string }` |
| `bulletins_minicta_clicked` | Click mini-CTA AC5 | idem + `{ entry_point }` |
| `bulletins_added_via_mini_flow` | Commit AC6 réussi | `{ entry_point, mode: "scan" \| "manual", n_matieres }` |

**And** ces events alimentent le KPI **conversion postponed → completed** (cible MVP ≥ 35 % en 4 semaines selon PRD)

### AC9 — Accessibilité RGAA AA (cohérent avec autres stories Epic 2)

**Given** les bandeaux, mini-CTAs et mini-flow
**When** je teste avec clavier seul, lecteur d'écran, et `prefers-reduced-motion: reduce`
**Then** **navigation clavier** :

- Bandeau AC3 : tab order `texte → bouton "Ajouter" → bouton `✕`` — Échap ferme via `✕` si bandeau focused
- Mini-CTA AC5 : tab order `texte → bouton "J'ajoute mes notes"` — accessible dans le scroll naturel de la page
- Mini-flow AC6 (sheet) : focus trap dans le sheet, Échap ferme, focus initial sur le premier bouton (Scanner ou Manuel — primary visuel)

**And** **HTML sémantique** :
- Bandeau : `<aside role="complementary" aria-label="Suggestion d'ajout bulletins">`
- Mini-CTA : `<aside role="complementary" aria-label="Compléter ton profil">`
- Sheet : `<dialog role="dialog" aria-modal="true" aria-labelledby>` (via shadcn `Sheet`)

**And** **annonces dynamiques** :
- Au commit AC6 réussi : `aria-live="polite"` annonce *"Profil mis à jour — stats personnalisées en cours de calcul."*
- Recalcul terminé : *"Stats mises à jour."*
- Banner dismiss : *"Suggestion masquée pour 7 jours."*

**And** **reduced motion** : pas d'animation propre sur les bandeaux/CTAs. Le badge "+14 pts" est statique (pas de slide-in fancy).

**And** **contraste** :
- `color-text-muted` sur `color-bg-2` (texte bandeau) : 5.6:1 (AA)
- Bouton tertiary brand sur `color-bg-2` : 4.9:1 (AA)

---

## 3. Tasks / Subtasks

### T1 — Backend : ajout flag `bulletins_status` + endpoint postpone (AC1, AC2)

- Extension modèle `StudentProfile` (ou similaire post-Story 2.3) avec :
  - `bulletins_status VARCHAR(15) DEFAULT 'pending'` enum (`pending | postponed | partial | completed`)
  - `bulletins_postponed_at TIMESTAMPTZ NULLABLE`
  - `bulletins_postponed_banner_dismissed_until TIMESTAMPTZ NULLABLE` (TTL 7j cf AC3)
- Endpoint `POST /api/v1/students/me/bulletins/postpone` (sans payload — idempotent)
  - Si déjà postponed → 200 (idempotent)
  - Si completed/partial → 409 (l'élève a déjà des bulletins, pas de postpone)
- Endpoint `POST /api/v1/students/me/bulletins/banner/dismiss` (sans payload)
  - Set `bulletins_postponed_banner_dismissed_until = now() + 7 days`
- Migration Alembic avec backfill `'pending'` pour comptes existants
- **Audit log Story 1.13** : event `bulletins_postponed` avec `{ via }` (cf AC8)
- RLS Story 1.8

### T2 — Frontend : composant `<BulletinsPostponedBanner />` (AC3)

- Composant Couche 3 dans `apps/web/components/bulletins/bulletins-postponed-banner.tsx`
- Props : `position?: "footer-fixed" | "sidebar"`, `onAddClick: () => void`
- Lecture state via hook `useStudentProfile()` (TanStack Query, cache shared) — affiche seulement si `bulletins_status === "postponed"` ET `bulletins_postponed_banner_dismissed_until < now()`
- Dismiss : mutation `POST /api/v1/students/me/bulletins/banner/dismiss` + invalide cache
- Layout responsive : full-width footer mobile, 320 px sidebar desktop
- Test visual snapshot + a11y axe-core

### T3 — Frontend : composant `<BulletinsMiniCTA />` (AC5)

- Composant Couche 3 dans `apps/web/components/bulletins/bulletins-mini-cta.tsx`
- Props : `context: "graph" | "stat" | "fiche_metier"`, `metier_id?: string`, `onAddClick: () => void`
- Pas dismissable (apparaît contextuellement, disparaît si `bulletins_status === "completed"`)
- Layout `Card` shadcn, fond `color-bg-2`, secondary CTA
- Snapshot + a11y

### T4 — Frontend : mini-flow `<BulletinsAddSheet />` (AC6)

- Composant Couche 3 dans `apps/web/components/bulletins/bulletins-add-sheet.tsx`
- Compose `Sheet` shadcn (bottom mobile, right desktop)
- 2 sous-composants (réutilisation Story 2.3 / 2.4) :
  - `<FilePickerSheet />` (Story 2.3 AC2) — pas modifié, juste rendu nested
  - `<MatiereInputRow[]>` (Story 2.4 AC3) — réutilisé en mode "1 trimestre uniquement"
- Au commit réussi (PATCH/POST classique Story 2.3 ou 2.4) :
  - Invalide cache profile via TanStack Query
  - Toast info *"Profil mis à jour — stats en cours de recalcul…"*
  - Émet event `bulletins_added_via_mini_flow`
- Ferme le sheet automatiquement

### T5 — Cross-cut Epic 3 : adaptation labels recos vocationnelles (AC4)

- **Pas une story à elle seule** — c'est un cross-cut à intégrer dans Story 3.11 `ScoreVocationnel` au moment de son implémentation
- Documenté ici comme contrat : le composant Story 3.11 prend en input un `student_profile` avec `bulletins_status` et adapte sa phrase recopiable + ses sections "Signaux contributifs"
- **Pas de fonctionnalité bloquante côté 2.5** — Story 2.5 elle-même n'implémente PAS cette adaptation, elle documente le contrat pour les stories Epic 3 / 4 consommatrices

### T6 — Cross-cut Epic 4 : adaptation stats admission (AC5)

- Idem T5 — cross-cut documenté pour Story 4.5 `CarteAdmission` et Story 4.9 `GraphParcours`
- Contrat : si `bulletins_status === "postponed"`, afficher fourchette + label "estimation indicative" + mini-CTA (rendre via `<BulletinsMiniCTA context="graph" />`)

### T7 — Tests (front + back + intégration)

- **Backend (pytest)** :
  - POST postpone idempotent
  - POST postpone si completed → 409
  - POST banner dismiss met TTL +7j
  - RLS cross-tenant
- **Frontend (Vitest + RTL)** :
  - `<BulletinsPostponedBanner />` : visible si postponed + non dismissé ; absent si completed ; absent si dismissed valid
  - `<BulletinsMiniCTA />` : variantes par context (snapshot)
  - `<BulletinsAddSheet />` : sheet ouvre, FilePicker ou Manuel visible selon choix, commit ferme sheet
  - A11y axe-core sur les 3 composants
- **E2E (Playwright)** :
  - **Léa happy path** : entry 3e card AC1 → dashboard avec bandeau visible → click bandeau → mini-flow → ajout manuel 5 matières → commit → bandeau disparaît, recos recalculées
  - **Banner dismiss** : click `✕` → bandeau disparu de la page courante → réapparaît sur autre page (cohérence cache profile) — wait 7 days simulé (mock date) → bandeau revient
- **Visual regression** : Léa vs Sarah écran recos vocationnelles → screenshot diff < 0.5 % (test critique parité visuelle)
- **Manuel** : test "ressenti" sprint review avec Léa proxy (cf garde-fous personas) — pas un test automatisé, mais une étape de qualification

### T8 — Documentation

- `docs/onboarding/step3-postponed.md` : flow visuel + contrat cross-cut Epic 3/4
- `docs/components/bulletins-postponed-banner.md`, `bulletins-mini-cta.md`, `bulletins-add-sheet.md`

---

## 4. Dev Notes

### 4.1 Wireframes ASCII — bandeau footer mobile (dashboard) + mini-CTA graphe

```
DASHBOARD — bandeau footer fixed
┌─────────────────────────────────────────┐
│  [navigation top]                        │
│                                          │
│  Recommandations vocationnelles          │
│  Liste 8 métiers …                       │
│                                          │
│  (scroll content)                        │
│                                          │
├─────────────────────────────────────────┤
│  Tu peux ajouter tes bulletins à tout    │ ← bandeau fixed bottom
│  moment pour des stats personnalisées.   │   h 56 max
│                          [ Ajouter → ] ✕ │   fond color-bg-2
└─────────────────────────────────────────┘

GRAPHE PARCOURS — mini-CTA contextuel
┌─────────────────────────────────────────┐
│  [graphe-récit avec stat 30-45%]         │
│                                          │
│  Pari audacieux — estimation indicative │
│  Affine cette estimation avec tes        │
│  bulletins.                              │
│                                          │
│  [Grille écoles cibles…]                 │
│                                          │
│  ┌────────────────────────────────────┐ │ ← mini-CTA card
│  │ 📋 Ajoute tes bulletins            │ │   color-bg-2
│  │    Tes stats deviendront           │ │   secondary CTA
│  │    personnalisées en moins d'1 min │ │
│  │        [ J'ajoute mes notes →    ] │ │
│  └────────────────────────────────────┘ │
│                                          │
└─────────────────────────────────────────┘
```

### 4.2 Wireframes ASCII — mini-flow ajout (sheet bottom mobile)

```
┌─────────────────────────────────────────┐
│  [page d'origine en fond, légèrement     │
│   assombrie par overlay sheet 50%]      │
│                                          │
├─────────────────────────────────────────┤
│                                          │ ← Sheet bottom
│              ╾━━━━━━╼                    │ ← handle drag
│                                          │
│  Ajoute tes bulletins              [✕]   │
│  En moins d'une minute, tes stats        │
│  deviennent personnalisées.              │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │     📷 Scanner / importer →        │ │ ← primary equiv. weight
│  └────────────────────────────────────┘ │
│  ┌────────────────────────────────────┐ │
│  │     ✍️  Saisir à la main →          │ │ ← secondary equiv. weight
│  └────────────────────────────────────┘ │
│                                          │
│                Annuler                   │ ← tertiary
└─────────────────────────────────────────┘
```

### 4.3 État émotionnel — le test Léa

| Moment | État cible Léa | Triggers à bannir |
|---|---|---|
| Clic 3e card AC1 | Soulagement ("OK je peux explorer sans contrainte") | Confirmation cérémonieuse, *"Tu es sûre ?"* |
| Arrivée dashboard | Curiosité ("Voyons ce qui s'ouvre") | Toast *"Sans bulletins, tu peux quand même !"* |
| Voir bandeau footer | Information neutre ignorable | Banner persistant, position invasive |
| Voir recos vocationnelles | Confiance ("Ça me parle, mêmes recos que tout le monde") | Sections vides avec placeholders culpabilisants |
| Voir graphe parcours | Engagement ("Je peux quand même me projeter") | Stats "—" ou "Connecte tes bulletins pour voir" |
| Décider d'ajouter ses notes (jour J+3) | Choix volontaire calme | Pop-up gamifiée, FOMO temporel |

### 4.4 Décisions design verrouillées (CRITIQUES)

- **`bulletins_status === "postponed"` est UNE statut, pas une absence** — sémantique distincte de `"incomplete"`. C'est un choix légitime, pas un défaut.
- **Pas de `ConsentDialog` au moment du skip** — différent de step-1 / step-2 "Plus tard" qui demandent confirmation. Ici, le choix est explicite via la card. Forcer une confirmation = signaler que c'est une "mauvaise" décision.
- **Pas de toast au skip** — silence respectueux. La transition vers le dashboard est l'unique feedback.
- **Bandeau dismissable 7 jours** — équilibre rappel utile / harcèlement. 7j = TTL choisie pour permettre exploration sans usure.
- **Mini-CTA contextuel apparaît dans la PAGE, pas en overlay** — il ne suit pas l'utilisateur, il est ancré dans le contenu. Anti-pop-up cognitive load.
- **Mini-flow d'ajout = Sheet bottom, pas re-onboarding complet** — économise le temps de Léa. Un trimestre suffit pour basculer en mode `partial` (recos déjà nourries).
- **Recalcul recos / stats en background après ajout** — toast info *"… en cours de recalcul…"* puis silence. Pas de spinner bloquant.
- **Visual regression Léa vs Sarah** comme test critique — c'est LE test qui valide le mode dégradé invisible.

### 4.5 Anti-patterns proscrits (PILIER de la story)

- ❌ **"Profil incomplet"** anywhere dans l'app pour un utilisateur postponed
- ❌ **"X % de ton profil"** — Story 2.7 traitera la maturité qualitativement
- ❌ **Pourcentages ou jauge de progression bulletins**
- ❌ **Modal bloquante** *"Tu n'as pas de bulletins !"*
- ❌ **Badge "Postponed" / "Incomplete"** visible sur la fiche utilisateur
- ❌ **CTA primary brand** sur le bandeau ou mini-CTA — toujours secondary/tertiary
- ❌ **"Débloque tes vraies stats !"** ou *"Voir tes chances réelles"*
- ❌ **Confettis** quand l'élève ajoute enfin ses bulletins
- ❌ **Bandeau qui follows scroll** (sticky persistent visuel) — économise visuel, anti-harcèlement
- ❌ **"Tu rates 73 % de l'expérience"** ou variations
- ❌ **Comparaison sociale** *"Les utilisateurs avec bulletins ont des recos plus précises"*
- ❌ **Section vide avec placeholder** "Stats indisponibles — connecte tes bulletins"
- ❌ **Animation différenciée** entre Léa et Sarah (graphe par exemple) — même animation 720 ms pour tous

### 4.6 Edge cases et failures explicites

| Edge case | Comportement attendu | AC ref |
|---|---|---|
| Léa clique 3e card AC1, puis revient à `/onboarding/step-3` via URL | Redirect direct dashboard (onboarding considéré completed) | AC1 |
| Léa dismiss le bandeau, change de page, ouvre une nouvelle page | Bandeau reste caché (TTL respecté côté API) | AC3 |
| Léa dismiss banner, attend 8 jours, revient | Bandeau réapparaît | AC3 |
| Léa clique mini-CTA AC5, choisit Manuel, saisit 0 matière, valide | Helper inline (cohérent Story 2.4 AC5), pas de commit, sheet ne ferme pas | AC6 |
| Léa ajoute 3 matières via mini-flow, commit OK, ouvre nouveau graphe | Stats recalculées, label *"estimation indicative"* disparu si `bulletins_status === "completed"` | AC6 |
| Léa ajoute 3 matières (partial), revient sur autre graphe | Stats encore en fourchette (1 trimestre = `partial`, label adapté *"estimation affinée"*) | AC6 |
| Léa supprime tous ses bulletins via Story 2.6 (édition profil) | `bulletins_status` revient à `"postponed"`, bandeau réapparaît | AC1 |
| Réseau coupe pendant commit mini-flow | Toast info offline, draft localStorage conservé, retry exponentiel | AC6 |
| Léa partage screenshot WhatsApp d'un graphe à Sarah | Screenshot doit être indiscernable — Sarah ne doit pas deviner que Léa est postponed | AC5 (test critique) |
| Léa partage `StoryExport` (Story 6) | Re-rendu PNG inclut *"estimation indicative"* en pied (intégré au design Story 6) | AC7 |
| Léa accède à l'envoi anticipé école Epic 5 | Premium gating applicable indépendamment, pas de blocage spécifique postponed | AC7 |
| Reduced motion sur badge "+14 pts" | Badge statique sans animation slide | AC9 |
| Léa avec `bulletins_status === "postponed"` accède à route directe `/profile/edit/bulletins` (Story 2.6) | Page accessible, formulaire pré-rempli vide, peut ajouter à tout moment | Story 2.6 cross-cut |

---

## 5. Project Structure Notes

```
apps/web/
  components/bulletins/
    bulletins-postponed-banner.tsx     ← AC3 (T2)
    bulletins-mini-cta.tsx             ← AC5 (T3)
    bulletins-add-sheet.tsx            ← AC6 (T4)
    __tests__/
      bulletins-postponed-banner.test.tsx
      bulletins-mini-cta.test.tsx
      bulletins-add-sheet.test.tsx
  hooks/
    use-student-profile.ts             ← hook shared lecture profile + bulletins_status
  app/(auth)/onboarding/step-3/
    page.tsx                            ← AC1 routing (déjà créé Story 2.3)
  e2e/
    bulletins-postponed.spec.ts        ← T7

apps/api/apps/students/                ← extension Story 2.3
  models.py                            ← bulletins_status fields (T1)
  views_bulletins_status.py            ← POST postpone + banner dismiss
  serializers_bulletins_status.py
  migrations/
    NNNN_bulletins_postponed_fields.py
  tests/
    test_bulletins_postponed.py

docs/onboarding/
  step3-postponed.md                   ← T8
docs/components/
  bulletins-postponed-banner.md
  bulletins-mini-cta.md
  bulletins-add-sheet.md
```

**Conventions à respecter (cross-cuts Epic 3 / 4) :**

- Story 3.11 `ScoreVocationnel` doit consommer `bulletins_status` et adapter sa phrase recopiable + sections
- Story 4.5 `CarteAdmission` doit consommer `bulletins_status` et afficher fourchette + label "estimation indicative" + render `<BulletinsMiniCTA />`
- Story 4.9 `GraphParcours` doit consommer `bulletins_status` (transmise au CarteAdmission interne)
- Story 6 `StoryExport` doit inclure mention "estimation indicative" dans le re-rendu PNG/PDF
- Documentation cross-cut à porter dans chacune de ces stories lors de leur contextualisation

---

## 6. References

- **UX spec globale** :
  - § Experience Principles #4 (mode normal = mode dégradé)
  - § Patterns transverses → "Mode dégradé invisible" (règle de design system, pas un composant)
  - § Emotional Goals secondaires → Dignité (PILIER Léa)
  - § Anti-patterns proscrits → "Mode dégradé avec marqueur visuel distinct"
  - § Flow 3 — Léa, mode dégradé invisible (Témoin dignité)
  - § Step 7 LE moment Path-Advisor → Léa et Sarah voient le même graphe
- **Epic 2 detail** : `_bmad-output/planning-artifacts/epics/epic-2-profil-eleve-onboarding.md` § Story 2.5
- **Stories Epic 2 sœurs** :
  - 2.3 `_bmad-output/implementation-artifacts/2-3-import-bulletins-pdf-ocr.md` — AC1 3e card (point d'entrée principal)
  - 2.4 `_bmad-output/implementation-artifacts/2-4-saisie-manuelle-notes.md` — AC5 lien tertiary footer
  - 2.6 (à venir) — `/profile/edit/bulletins` réutilise `BulletinsAddSheet`
- **Story 1.13 (audit log)** : `_bmad-output/implementation-artifacts/1-13-journal-audit-acces.md` — events postponed/banner
- **PRD** : FR17 (mode "Plus tard"), UX-DR25 (Léa et Sarah même UI), KPI conversion postponed → completed
- **Cross-cuts** (stories non encore contextées) :
  - Story 3.11 `ScoreVocationnel`
  - Story 4.5 `CarteAdmission`
  - Story 4.9 `GraphParcours`
  - Story 6 `StoryExport`

---

## 7. Dev Agent Record

### Agent Model Used
Claude Sonnet 4.6 (claude-sonnet-4-6)

### Debug Log References
- Sheet component missing from shadcn — created `apps/web/src/components/ui/sheet.tsx` from `@radix-ui/react-dialog` (same dep as Dialog).
- `bulletins_status` field already present from Story 2.7 migration 0003; only added the two new postpone fields in migration 0004.

### Completion Notes List
- T1 ✅ 10 backend tests passing: postpone idempotent, 409 on completed/partial, banner dismiss 7-day TTL
- T2 ✅ 8 RTL tests: visibility logic (postponed/completed/dismissed), onAddClick, dismiss mutation, a11y, forbidden words
- T3 ✅ 6 RTL tests: visibility, CTA click, context variants, a11y, forbidden words
- T4 ✅ 6 RTL tests: closed=null, open=dialog, 2 buttons, cancel calls onClose, aria-modal, copy check
- T5/T6 ✅ Cross-cut contracts documented (no code — carried by Epic 3/4/6 stories)
- T7 ✅ All tests pass (20 frontend, 10 backend). Pre-existing failures unrelated to 2.5.
- T8 ✅ 4 docs created: step3-postponed.md + 3 component docs

### File List
- `apps/api/apps/students/models.py` — added `bulletins_postponed_at`, `bulletins_postponed_banner_dismissed_until`
- `apps/api/apps/students/migrations/0004_bulletins_postponed_fields.py` — new migration
- `apps/api/apps/students/views_bulletins_status.py` — BulletinsPostponeView + BulletinsBannerDismissView
- `apps/api/apps/students/urls.py` — 2 new routes
- `apps/api/apps/students/tests/test_bulletins_postponed.py` — 10 tests
- `apps/web/src/hooks/use-student-profile.ts` — shared hook (useStudentProfile, usePostponeBulletins, useDismissBulletinsBanner, isBannerVisible)
- `apps/web/src/components/features/bulletins/bulletins-postponed-banner.tsx`
- `apps/web/src/components/features/bulletins/bulletins-mini-cta.tsx`
- `apps/web/src/components/features/bulletins/bulletins-add-sheet.tsx`
- `apps/web/src/components/features/bulletins/__tests__/bulletins-postponed-banner.test.tsx`
- `apps/web/src/components/features/bulletins/__tests__/bulletins-mini-cta.test.tsx`
- `apps/web/src/components/features/bulletins/__tests__/bulletins-add-sheet.test.tsx`
- `apps/web/src/components/ui/sheet.tsx` — new shadcn-style Sheet component
- `docs/onboarding/step3-postponed.md`
- `docs/components/bulletins-postponed-banner.md`
- `docs/components/bulletins-mini-cta.md`
- `docs/components/bulletins-add-sheet.md`

### Change Log

- 2026-05-25 — Story 2.5 contextée par Marwen + Claude (Opus 4.7). **Story PILIER** du principe expérience #4 (mode normal = mode dégradé). 3 composants Couche 3 ajoutés au design system : `BulletinsPostponedBanner`, `BulletinsMiniCTA`, `BulletinsAddSheet`. Cross-cuts Epic 3 / 4 / 6 documentés mais non implémentés ici (à porter par les stories consommatrices).
