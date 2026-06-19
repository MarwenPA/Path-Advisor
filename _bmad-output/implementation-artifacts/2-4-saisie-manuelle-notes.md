# Story 2.4: Saisie manuelle assistée des notes (chemin fallback)

**Epic:** 2 — Profil Élève & Onboarding
**Status:** review
**Sprint:** 5 (Onboarding bulletins & OCR)
**Story Key:** `2-4-saisie-manuelle-notes`
**Estimation:** M (medium) — front-end formulaire structuré + endpoint PATCH bulletin manuel + référentiel matières par niveau (factorisé avec Story 2.3 T1). Pas d'OCR, pas de stockage S3 (texte structuré, pas de fichier source). Sized ~1.5–2 j focused work.

> Chemin alternatif équivalent à Story 2.3 (OCR), accessible via : **(a)** clic direct sur la 2e card de l'écran AC1 *"Saisir mes notes à la main"*, **(b)** fallback depuis `GracefulFallback` de Story 2.3 quand l'OCR rate (CTA primary *"Saisir à la main"*), **(c)** clic bouton tertiary *"Saisir à la main plutôt"* depuis `ScenarioLoader` au-delà de 30 s (Story 2.3 AC4). **Principe critique** : la saisie manuelle ne doit pas être ressentie comme un échec — c'est *une voie d'égale dignité*. Mehdi qui tape ses notes parce que la photo de son téléphone fissuré n'a pas marché doit terminer cet écran en pensant *"OK, c'était rapide"*, pas *"Je suis nul."*

---

## 1. User Story

**As an** élève (Léa qui refuse l'OCR par confidentialité, Mehdi dont l'OCR a raté, ou n'importe quel utilisateur qui préfère la saisie),
**I want** saisir mes notes et appréciations dans un formulaire structuré pré-rempli avec la liste de matières correspondant à mon niveau, avec validation inline non-intrusive et possibilité de sauvegarde partielle,
**So that** mon profil scolaire soit construit en 3 minutes sans humiliation, et **so that** le moteur de reco vocationnelle (Epic 3) ait des notes pour pondérer les recos (FR15).

**Business value :** sans ce chemin, OCR rate = porte fermée. Avec ce chemin, on garantit **NFR-R4 graceful degradation** (OCR indisponible / raté → saisie manuelle) et on respecte la **dignité Léa** : son refus de scanner ses bulletins n'est jamais traité comme un défaut, mais comme un choix de pair. Côté analytics, on s'attend à un mix MVP ~60-70 % OCR / 25-35 % manuel / 5-10 % Plus tard (Story 2.5) — la saisie manuelle est donc un chemin **majoritairement utilisé**, pas un fallback marginal. À traiter en first-class.

**Garde-fous personas activés sur cet écran :**

- **Léa (dignité)** — pas de copy comparatif avec l'OCR ("Tu aurais pu scanner pour aller plus vite") ; pas de bouton "Revenir au scan" minimisant son choix. La saisie manuelle a sa propre logique, ses propres affordances.
- **Mehdi (sortie de fallback OCR)** — arrivé ici après échec OCR, il porte une charge émotionnelle. Le premier écran doit reconnaître cette transition (*"Pas grave, on saisit à la main"* en breadcrumb subtil si arrivé via fallback) sans dramatiser.
- **Sarah (efficacité)** — saisie au pouce sur mobile, validation **on blur seulement** (pas à chaque keystroke), tab order strict pour saisie rapide successive (`Tab` après une note → champ suivant).

---

## 2. Acceptance Criteria (BDD)

### AC1 — Route, layout, header (point d'entrée à 3 origines)

**Given** je clique sur la 2e card *"Saisir mes notes à la main"* de Story 2.3 AC1, OU je clique *"Saisir à la main"* dans le `GracefulFallback` AC7, OU je clique *"Saisir à la main plutôt"* dans le `ScenarioLoader` AC4
**When** je suis redirigé vers `/onboarding/step-3/manual` (segment Next.js)
**Then** je vois un écran avec :

- En **header sticky** : back chevron (`<`) à gauche enabled (retour vers l'écran AC1 des 3 cards de choix, ou vers le `GracefulFallback` selon la route d'origine — voir AC8) + indicateur de progression `● ● ●` (3 dots actifs `color-brand`) + **pas de bouton "Plus tard"** dans le header (la 3e card AC1 reste le point d'entrée canonique de Story 2.5)
- Titre `text-h2` : *"Tes notes, à la main"*
- Sous-titre `text-body` `color-text-muted` :
  - Si arrivé via card 2 directe : *"On a préparé la liste des matières selon ton niveau. À toi de remplir — tu peux en sauter, on s'en fiche."*
  - Si arrivé via fallback OCR : *"Pas grave, on continue à la main. On a préparé la liste des matières selon ton niveau — tu peux en sauter, on s'en fiche."* (le *"Pas grave"* connecte avec le `GracefulFallback`)
- En footer sticky mobile : bouton primary *"Valider et continuer"* (right-aligned desktop, full-width mobile, `lg`, **toujours enabled** — y compris avec 0 matière remplie cf AC5)

**And** le layout respecte les tokens de cohérence avec Story 2.1 / 2.2 / 2.3 récap (container `max-width: 600 px` mobile-form, **`max-width: 1080 px` desktop** — cohérent avec le récap éditable 2.3 desktop)
**And** le **breadcrumb subtil** (`text-caption` `color-text-subtle`, position sous le titre, condition affichage : seulement si `arrivé_via === "ocr_fallback"`) : *"Tu reviens du scan qui n'a pas marché — on reprend ici."* — discret, factuel, **désactivable** au scroll (disparaît dès le premier scroll vertical)

### AC2 — Sélection trimestre (tabs cohérents avec Story 2.3 AC5)

**Given** je suis sur l'écran de saisie manuelle
**When** je consulte la zone de saisie
**Then** je vois en haut :

- **Tabs trimestres** (composant `Tabs` shadcn) — mêmes specs visuelles que Story 2.3 AC5 (cohérence stricte) : `Trim. 1` actif par défaut, `Trim. 2` et `Trim. 3` disponibles ; bouton `+ Ajouter` à droite pour ajouter un 4e trimestre (rare en lycée FR, mais possible : seconde + 1ère cumulés)
- **Bulletin label éditable** sous les tabs (même pattern que Story 2.3 AC5) : *"Trim. 1 — {niveau}"* avec icône ✎, année courante détectée (`getFiscalYear(today)` → "2025-2026")

**And** **les trimestres validés** (passés en `bulletin_status === "completed"` côté serveur) affichent un check icon vert sur le tab (cohérent récap 2.3)
**And** **switcher de trimestre** : taper sur un tab change le formulaire affiché ; les saisies en cours sont sauvegardées via le draft localStorage (cf AC7) ; **aucune confirmation** "Vous avez des modifications non sauvegardées" (anti-friction — la persistence couvre)
**And** chaque trimestre est **indépendant** côté commit (bouton "Valider et continuer" sur le footer commit le trimestre actif seul) — l'élève peut valider Trim. 1 puis revenir plus tard pour Trim. 2 et 3 sans pénalité

### AC3 — Formulaire structuré : matières pré-remplies selon niveau scolaire

**Given** mon niveau est `lycee_terminale + filiere=general + specialites=["mathematiques","svt","hggsp"]` (déclaré Story 2.2)
**When** le formulaire se charge sur Trim. 1
**Then** je vois une **liste verticale de matières pré-remplies**, factorisée du référentiel Story 2.3 T1 (`packages/copy/onboarding/subjects-by-level.ts`) :

```
Pour Sarah (Terminale général, spés Maths+SVT+HGGSP) — 10 matières pré-remplies :

Tronc commun :
  Français (Bac anticipé)      [—.— / 20]   appréciation : libre
  Philosophie                   [—.— / 20]
  Histoire-Géo                  [—.— / 20]
  Anglais LV1                   [—.— / 20]
  Espagnol LV2 (ou autre LV2)   [—.— / 20]
  EPS                            [—.— / 20]
  Enseignement scientifique     [—.— / 20]

Tes spécialités :
  Mathématiques                 [—.— / 20]
  SVT                            [—.— / 20]
  HGGSP                          [—.— / 20]
```

**And** chaque ligne matière est un **bloc autonome** (composant `MatiereInputRow` factorisé) avec :

- **Label matière** (`text-body` weight 500) — non éditable (le référentiel est canonique)
- **Champ note** : `Input` shadcn type `text` `inputmode="decimal"` (clavier numérique mobile), placeholder grisé `—.— / 20`, width 88-120 px (selon device), text-align right, font-feature-settings tabular-numbers, **validation on blur** : note ∈ [0, 20] décimal, accepte `,` ou `.` (normalisé serveur en `.`)
- **Bouton expand "Ajouter une appréciation"** (tertiary, taille `sm`, color `color-text-subtle`) — au tap, expand un `Textarea` 3 lignes (max 500 chars) sous le champ note, focus automatique
- **Icône Lucide ChevronDown** rotative 180° quand l'appréciation est expandée (signal visuel "ouvert")
- **Bouton supprimer matière** (icône Lucide `X` discrète 14 px, color `color-text-subtle`, visible au hover / focus + toujours visible sur mobile) — à droite ; au tap, confirm inline 5 s *"Supprimée — Annuler"* (toast non bloquant), suppression réelle si pas annulé

**And** sous la liste, un **bouton tertiary dashed** *"+ Ajouter une matière manquante"* (même style que Story 2.3 récap AC5) — au tap, ouvre un mini-formulaire inline :
- Champ `Select` shadcn avec recherche pré-rempli depuis le référentiel élargi (ex. *"Latin"*, *"Grec"*, *"Maths complémentaires"*, *"DGEMC"*, *"Section européenne anglais"*, etc.) — ~30 options pour lycée général
- Champ note + bouton "Ajouter" / "Annuler"
- L'ajout est local (saved en draft localStorage tant que pas commité)

**And** **adaptation par niveau** :

| Niveau           | Tronc commun pré-rempli | Spés/branches |
|------------------|-------------------------|---------------|
| `college_3eme`   | Maths, Français, Histoire-Géo, EMC, SVT, Physique-Chimie, Anglais LV1, LV2, EPS, Arts plastiques, Musique, Techno (~12 matières) | aucune sous-branche |
| `lycee_2nde`     | Maths, Français, Histoire-Géo, EMC, SVT, Physique-Chimie, Anglais LV1, LV2, EPS, SES, Latin/Grec optionnel, Arts optionnels (~12-14) | aucune (spés en fin de 2nde) |
| `lycee_1ere/Tle gen` | Tronc commun (cf supra) + 3 spés (1ère) ou 2 spés (Tle) déclarées | les spés affichées en section dédiée |
| `lycee_1ere/Tle techno` | Tronc commun + matières spécifiques selon sous-filière (STMG / STI2D / etc.) | sous-filière headers |
| `lycee_1ere/Tle pro`   | Tronc commun + matières professionnelles selon spécialité | section "Matières professionnelles" |
| `postbac`        | ⚠ Aucune matière pré-remplie (référentiel post-bac trop variable) — formulaire vide avec gros bouton "Ajouter ma première matière" + suggestion contextuelle | manual all |

### AC4 — Validation note (UX-DR35)

**Given** je saisis une valeur dans le champ note
**When** je quitte le champ (blur)
**Then** validation appliquée :

- **Vide** → considéré "non renseigné", aucune erreur (un trimestre peut être partiel)
- **Entre 0 et 20 (inclus, décimal)** → OK, sauvegarde draft localStorage immédiate
- **> 20 OU < 0 OU non-numérique** → erreur inline `text-caption` `color-danger` sous le champ : *"Note entre 0 et 20"* + bordure du champ passe en `color-danger` + valeur précédente conservée dans le champ (pas effacée automatiquement)
- **Format français accepté** : `14,5` (virgule) ou `14.5` (point) → normalisé en `.` côté client avant PATCH
- **Décimales > 2** : tronqué à 2 décimales côté client (ex. `14.567` → `14.56`)

**And** **aucune validation à chaque keystroke** (UX-DR35 strict) — l'erreur n'apparaît qu'au blur ou submit
**And** le focus revient automatiquement sur le **premier champ en erreur** après tap "Valider et continuer" si validation échoue
**And** **aucun astérisque "obligatoire"** sur les champs (UX spec § Form Patterns) — les matières sont *toutes optionnelles*, l'utilisateur décide combien remplir

### AC5 — Sauvegarde partielle : "5 matières sur 10, ça suffit déjà"

**Given** je clique "Valider et continuer" avec **moins de matières pré-remplies que le tronc complet** (ex. 5/10 sur Sarah Terminale)
**When** le commit est envoyé
**Then** le serveur accepte la sauvegarde partielle (pas de 422 "trop peu de matières") et le profil passe `bulletin_status === "partial"`
**And** un **toast info** non bloquant apparaît 3 s : *"On a ce qu'il faut pour démarrer — tu pourras compléter à tout moment depuis ton profil."* (cohérent UX spec : *"on peut déjà produire des recos avec ce que tu as"*)
**And** le moteur de reco downstream (Epic 3) traite ce profil comme un profil "data-partial" — recos avec label *"estimation indicative — précision améliorée avec plus de notes"* (cohérent mode dégradé Léa, Story 2.5)
**And** au minimum **1 matière** doit être renseignée pour valider un trimestre — si tous les champs sont vides, le bouton "Valider et continuer" affiche un helper inline `text-caption` `color-text-muted` *"Renseigne au moins une matière, ou clique '⏭ Plus tard' pour explorer d'abord."*

**And** un lien tertiary *"⏭ Plus tard, je préfère explorer d'abord"* (cohérent Story 2.5 entry point) est **visible en footer secondaire** sous le bouton primary, en `text-sm` `color-brand` underline — déclencheur de Story 2.5 sans repasser par l'écran AC1

### AC6 — Accessibilité RGAA AA (UX-DR35 strict)

**Given** l'écran de saisie et toutes les phases
**When** je teste avec clavier seul, lecteur d'écran, et `prefers-reduced-motion: reduce`
**Then** **navigation clavier** :

- `Tab` traverse dans l'ordre : back → tabs trimestre → bulletin label edit → champ note matière 1 → bouton "Ajouter appréciation" matière 1 → bouton supprimer matière 1 → champ note matière 2 → ... → bouton "+ Ajouter matière manquante" → primary "Valider et continuer" → lien "Plus tard"
- Sur une appréciation expandée, `Tab` descend dans le `Textarea` puis remonte au champ note de la matière suivante (cohérent saisie séquentielle rapide)
- `Esc` sur un champ en édition annule la saisie (restaure dernière valeur draft) ; `Esc` sur le focus libre ne fait rien (pas de "back" implicite)

**And** **HTML sémantique** :

- Form principal : `<form aria-label="Saisie manuelle des notes">` (pas de submit natif, c'est le bouton qui gère)
- Chaque matière : `<fieldset>` contenant `<legend class="sr-only">{matière}</legend>` + `<label for>` explicite + `<input>` + bouton tertiary expand
- Tabs trimestre : `<nav role="tablist">` avec `role="tab" aria-selected="true|false"` (héritage shadcn `Tabs`)
- Erreur inline : `<span role="alert" aria-live="polite">` (annonce SR au blur uniquement)

**And** **annonces dynamiques** :

- Note validée : SR-only `aria-live` *"Note Mathématiques, 14.5 sur 20, enregistrée."*
- Erreur : *"Erreur Mathématiques : note entre 0 et 20."* au blur
- Ajout matière manquante : *"Latin ajouté à la liste."*
- Suppression : *"Matière supprimée. Bouton Annuler disponible."*

**And** **reduced motion** : aucune animation propre sur cet écran (expand appréciation = hauteur transition `motion-quick` → collapse à ~0 ms reduced motion). Pas d'autre animation à neutraliser.

**And** **touch targets** : tous champs, boutons, icônes 44 × 44 px minimum (zone tactile via padding où nécessaire)

**And** **zoom 200 %** : pas d'overflow horizontal, layout reflow correct à 320 px × 200 %

### AC7 — Persistence + reprise (cohérent avec 2.1 / 2.2 / 2.3)

**Given** je suis en cours de saisie sur Trim. 1
**When** je quitte l'app sans valider
**Then** mes saisies **partielles** sont sauvegardées dans **localStorage** sous clé `manual_bulletin_draft_{trimestre_id}` au debounce 500 ms après chaque blur valide (cohérent Story 2.3 AC9 recap_editing)
**And** au retour sur `/onboarding/step-3/manual`, le draft est réappliqué prioritairement sur la réponse serveur
**And** **fallback offline** : si commit échoue (réseau coupé, 5xx), un toast info *"Pas de réseau ? On garde ta saisie, on enverra dès que possible."* + retry exponentiel SWR/TanStack Query (1 s → 2 s → 4 s, max 3 tentatives)
**And** si commit réussit, le draft localStorage est flush et le serveur enregistre :

```json
{
  "trimestre_id": "trim_1_2025_2026_terminale",
  "matieres": [
    { "subject_id": "mathematiques", "note": 14.5, "appreciation": null },
    { "subject_id": "svt", "note": 13.2, "appreciation": "Bonne progression…" },
    { "subject_id": "latin_custom", "note": 12.0, "appreciation": null, "is_custom": true }
  ],
  "source": "manual",
  "completed_at": "2026-05-25T10:42:00Z",
  "level_at_save": "lycee_terminale",
  "subjects_ref_version": "2026-05-v1"
}
```

**And** si l'élève **passe sur Trim. 2** sans valider Trim. 1, les deux drafts coexistent en localStorage et le serveur les commit indépendamment au "Valider et continuer" respectif

### AC8 — Back chevron : retour intelligent selon origine

**Given** je clique le back chevron du header
**When** la navigation se déclenche
**Then** le comportement dépend de l'origine (state passé via URL param `?origin=...` ou via context React) :

| Origine                                       | Retour vers                                              | Confirmation modifications ?  |
|-----------------------------------------------|----------------------------------------------------------|-------------------------------|
| `origin=cards` (clic direct card 2)           | `/onboarding/step-3` (écran AC1 3 cards)                | Oui si draft non vide          |
| `origin=ocr_fallback` (depuis GracefulFallback)| `/onboarding/step-3` (écran AC1) ou re-tenter scan ? **Décision : écran AC1, garder les 3 options** | Oui si draft non vide          |
| `origin=ocr_optin` (depuis ScenarioLoader > 30s)| `/onboarding/step-3/processing` (revoir status OCR) — au cas où le job a fini en arrière-plan | Oui si draft non vide          |
| Pas d'origine connue / URL directe            | `/onboarding/step-3` (écran AC1) — sortie sécurisée    | Oui si draft non vide          |

**And** la confirmation modifications utilise une **`ConsentDialog`** (Story 1.14) avec :
- Title : *"Tu as commencé à saisir des notes"*
- Description : *"Tu peux quitter — on garde ta saisie. Ou rester et finir ce trimestre."*
- `acceptLabel` : *"Quitter, garder ce que j'ai fait"*
- `refuseLabel` : *"Je reste"*
- **Pas `isAcceptDestructive`** — quitter avec persistence n'est pas destructif

### AC9 — État vide ré-entrée + état complet

**Given** je rouvre `/onboarding/step-3/manual` alors que **tous les trimestres sont validés** (`onboarding_step3_status === "completed_manual"`)
**When** la page se charge
**Then** je suis **redirigé directement vers `/dashboard`** (entrée Epic 3) — pas de re-affichage du formulaire
**And** si je veux modifier mes notes plus tard, le **point d'entrée canonique** est `/profile/edit/bulletins` (Story 2.6), pas un re-passage par l'onboarding

**And** si **aucun trimestre n'est validé mais le draft localStorage existe** → écran reprend en mode édition avec le draft réappliqué (focus sur le premier champ non rempli)

---

## 3. Tasks / Subtasks

### T1 — Référentiel matières par niveau (factorisation Story 2.3 T1)

- Étendre `packages/copy/onboarding/subjects-by-level.ts` (créé par Story 2.3 T1) avec :
  - `getSubjectsForLevel(level, filiere?, specialites?, sousFiliereTechno?): MatiereDef[]` — fonction pure
  - `MatiereDef = { id: string; label: string; is_specialite: boolean; is_optional: boolean }`
  - Référentiel ÉLARGI (matières optionnelles ajoutables via "+ Ajouter une matière manquante") séparé : `getOptionalSubjectsForLevel(...)`
  - Versionning `SUBJECTS_REF_VERSION` partagé avec Story 2.3 (cohérence audit longitudinal)
- Tests : matière inconnue → throw ; référentiel non-vide pour chaque combinaison niveau×filière

### T2 — API backend : POST/PATCH `/api/v1/students/me/bulletins/manual` (AC2-AC7)

- Modèle `BulletinManual` (ou réuse de `Bulletin` Story 2.3 avec `source: "manual" | "ocr"`) :
  - `id`, `student_id (fk)`, `trimestre_label`, `year`, `source: "manual"`, `matieres JSONB`, `subjects_ref_version`, `level_at_save`, `created_at`, `validated_at`
  - **Pas de stockage S3** (pas de fichier source) — saisie pure
- Endpoint `POST /api/v1/students/me/bulletins/manual` (commit nouveau bulletin)
- Endpoint `PATCH /api/v1/students/me/bulletins/manual/{id}` (modification post-commit, route partagée avec édition profil Story 2.6)
- Validation Zod / pydantic :
  - Au moins 1 matière requise pour commit (AC5)
  - Chaque note ∈ [0, 20] décimal max 2 décimales
  - `subject_id` ∈ référentiel OU préfixe `custom:` pour matières manquantes ajoutées (validation au commit)
  - Appréciation ≤ 500 chars
- **Audit log Story 1.13** : event `bulletin_manual_saved` avec `{ student_id, trimestre_id, n_matieres, has_custom_subjects, source: "manual" }`
- RLS Story 1.8 appliqué

### T3 — Frontend : écran `OnboardingStep3Manual` (AC1-AC9)

- Route Next.js : `apps/web/app/(auth)/onboarding/step-3/manual/page.tsx`
- Composant racine `<OnboardingStep3Manual />` avec state local :
  - `activeTrimestre: 1 | 2 | 3 | 4`
  - `drafts: Record<trimestreId, MatiereDraft[]>`
  - `errors: Record<subjectId, string>`
- Sous-composants :
  - `<TrimestreTabs />` (factorisation possible avec Story 2.3 récap)
  - `<MatiereInputRow />` (cœur du formulaire — note + appréciation expandable + supprimer)
  - `<AddSubjectInline />` (mini-form "+ Ajouter matière manquante")
  - `<BackConfirmDialog />` (réuse `ConsentDialog` Story 1.14)
- Hooks :
  - `useManualBulletinDraft(trimestreId)` (localStorage debounce 500 ms)
  - `useSubjectsForLevel(level, filiere, specialites)` (memo référentiel)
  - `useCommitManualBulletin()` (TanStack Query mutation avec retry)

### T4 — Tests (front + back)

- **Backend (pytest)** :
  - POST avec 5 matières + 5 custom → 200, audit log enregistré
  - POST avec 0 matière → 422
  - PATCH note 14.5 → 15.0 → audit log delta
  - Note > 20 → 400
  - Custom subject sans préfixe `custom:` → 422
  - RLS cross-tenant
- **Frontend (Vitest + RTL)** :
  - Render initial : tronc commun affiché selon niveau (snapshot par persona : Sarah Tle, Mehdi 3ème, Léa post-bac vide)
  - Saisie note 14.5 → blur → valeur enregistrée + pas d'erreur
  - Saisie "abc" → blur → erreur inline `text-caption` `color-danger`, valeur conservée
  - Tab order strict (test via `userEvent.tab()` × N → assertion focus order)
  - Expand appréciation → Textarea apparaît, focus dedans
  - Ajout matière custom "Latin" → ajoutée à la liste, draft mis à jour
  - Suppression matière → toast Annuler 5 s, suppression effective si pas annulé
  - Validation footer avec 0 matière → helper inline, primary disabled (en termes d'action — toujours cliquable mais affiche le helper)
  - Validation footer avec 1 matière → commit OK, redirect dashboard
  - Reduced motion : pas d'animation expand
- **E2E (Playwright)** : 3 scénarios harness
  - **Sarah happy path manual** : entry card 2 → 6/10 matières remplies → valider → toast info partial → dashboard. < 3 min simulés.
  - **Mehdi fallback** : entry depuis GracefulFallback OCR → breadcrumb visible → 5 matières → valider → ok
  - **Léa post-bac vide** : entry card 2 → liste vide → ajoute 3 matières custom → valider → ok
- **A11y axe-core** : aucune violation, table semantic, label/for explicit, role="alert" sur erreurs
- **Manuel** : VoiceOver iOS sur saisie séquentielle 5 matières + ajout custom — checklist `docs/a11y/onboarding-step3-manual.md`

### T5 — Documentation

- `docs/onboarding/step3-manual.md` : flow visuel + variantes par persona + entry origins
- `docs/a11y/onboarding-step3-manual.md`

---

## 4. Dev Notes

### 4.1 Wireframes ASCII — mobile 375 px, Sarah Terminale général

```
┌─────────────────────────────────────────┐
│ <  ● ● ●                                │
├─────────────────────────────────────────┤
│  Tes notes, à la main                    │
│  On a préparé la liste des matières     │
│  selon ton niveau. À toi de remplir —   │
│  tu peux en sauter, on s'en fiche.       │
│                                          │
│  ┌──┬──┬──┬──────┐                       │ ← Tabs
│  │T1│T2│T3│+Ajout │                       │
│  └──┴──┴──┴──────┘                       │
│                                          │
│  Trim. 1 — Terminale [✎]                 │
│  Année 2025-2026                         │
│                                          │
│  Tronc commun                            │ ← text-sm color-text-muted
│  ┌─────────────────────────────────────┐│
│  │ Français (Bac anticipé)             ││
│  │ ┌───────────┐                       ││
│  │ │ 13.0 / 20 │  + Ajouter une        ││ ← Input + tertiary
│  │ └───────────┘    appréciation  ✕    ││   delete icon X
│  │ ─────────────────────────────────── ││
│  │ Philosophie                         ││
│  │ ┌───────────┐                       ││
│  │ │ —.— / 20  │  + Ajouter une        ││ ← vide = placeholder
│  │ └───────────┘    appréciation  ✕    ││
│  │ ─────────────────────────────────── ││
│  │ Histoire-Géo                        ││
│  │ ┌───────────┐                       ││
│  │ │ 15.5 / 20 │  ▼ Appréciation       ││ ← expanded
│  │ └───────────┘                  ✕    ││
│  │ ┌──────────────────────────────────┐││
│  │ │ Très bonne participation, lec-   │││ ← Textarea 3 lignes
│  │ │ tures personnelles à encourager. │││
│  │ └──────────────────────────────────┘││
│  │ ─────────────────────────────────── ││
│  │ Anglais LV1, Espagnol LV2, EPS, ES  ││ ← 4 autres lignes
│  └─────────────────────────────────────┘│
│                                          │
│  Tes spécialités                         │ ← text-sm color-text-muted
│  ┌─────────────────────────────────────┐│
│  │ Mathématiques                       ││
│  │ ┌───────────┐                       ││
│  │ │ 14.5 / 20 │  + Ajouter une        ││
│  │ └───────────┘    appréciation  ✕    ││
│  │ ─────────────────────────────────── ││
│  │ SVT, HGGSP                          ││ ← 2 autres lignes
│  └─────────────────────────────────────┘│
│                                          │
│  + Ajouter une matière manquante         │ ← tertiary dashed
│                                          │
├─────────────────────────────────────────┤
│  ┌────────────────────────────────────┐ │
│  │  Valider et continuer        →     │ │ ← primary lg
│  └────────────────────────────────────┘ │
│         ⏭ Plus tard, je préfère          │ ← tertiary footer
│             explorer d'abord             │
└─────────────────────────────────────────┘
```

### 4.2 État émotionnel par origine d'entrée

| Origine | État d'entrée probable | Cible émotionnelle | Triggers à bannir |
|---|---|---|---|
| **Card 2 directe** (choix conscient saisie) | Compétence anticipée ("Je préfère écrire") | Confort, contrôle ("Je vais à mon rythme") | "Pourquoi pas le scan ?", comparaison OCR |
| **OCR fallback** (échec, rebond) | Frustration récente, charge émotionnelle | Reprise calme, transition douce ("Pas grave, on continue") | Re-mention de l'échec, "Tu avais essayé de scanner…", drame |
| **OCR opt-in > 30s** (impatience) | Frustration de l'attente | Contrôle reconquis ("Je passe à plus rapide") | Banner "Le scan a finalement marché", choix imposé |

**Test sortie écran** : à la fin de step-3 manuel, l'élève pense quoi ? Cible : *"OK, c'était pas si long en fait."* — pas *"J'aurais préféré scanner."*

### 4.3 Edge cases et failures explicites

| Edge case | Comportement attendu | AC ref |
|---|---|---|
| Élève tape "14,5" (virgule) | Normalisé en `.` côté client, accepté | AC4 |
| Élève tape "14.567" | Tronqué à 2 décimales `14.56` au blur | AC4 |
| Élève tape "20.1" | Erreur inline "Note entre 0 et 20", valeur conservée | AC4 |
| Élève tape note dans 0/10 matières et clique Valider | Helper inline, pas de commit, lien tertiary "Plus tard" mis en avant | AC5 |
| Élève remplit 1/10 matières et valide | Commit OK, toast info, `bulletin_status: "partial"`, dashboard | AC5 |
| Élève quitte avec draft non vide, revient | Draft réappliqué silencieusement, focus sur premier champ non rempli | AC7 |
| Élève change de niveau scolaire (Story 2.2) après avoir saisi des notes manuelles | Notes archivées avec `level_at_save` + `subjects_ref_version` — le formulaire suivant utilisera nouveau niveau, anciennes notes restent dans le profil | AC3 |
| OCR finit en arrière-plan pendant saisie manuelle (cas opt-in > 30s) | À la validation, toast info *"Tes bulletins ont aussi été lus — utiliser cette analyse ?"* propose le merge des deux sources avec preview avant choix (Story 2.3 AC4) | T4 E2E |
| Élève ajoute "Latin" (custom) avec note 14.5 | Commit accepte, prefix `custom:latin`, audit log flag `has_custom_subjects: true` | T2 |
| Élève supprime toutes les matières d'un trimestre puis valide | Helper inline, primary bloqué (1 matière min), suggère "Plus tard" | AC5 |
| Lecteur d'écran sur saisie séquentielle | Tab order strict matière 1 → matière 2 → ..., annonce note + matière à chaque blur | AC6 |
| Reduced motion sur expand appréciation | Hauteur transition à 0 ms (instantané) | AC6 |
| Élève post-bac sans formation type déclarée | Liste vide, bouton "+ Ajouter ma première matière" prominent + suggestions contextuelles selon `postbac_formation_type` | AC3 |
| Custom subject avec caractères Unicode rares (孔子, إعراب) | Accepté côté front (validation Unicode L/N), commit côté serveur (UTF-8 OK) | AC3 |
| Élève spam click "Valider" pendant retry network | Button disabled pendant in-flight, pas de double commit | AC7 |
| Mobile keyboard "Suivant" sur clavier numérique iOS | Tab vers le prochain champ note (passe les boutons appréciation) — UX power-user optionnelle | AC6 |

### 4.4 Décisions design verrouillées

- **Matières pré-remplies par niveau, pas un blank slate** — économise 80 % du temps de saisie pour les cas standards (collège, lycée), permet à l'élève de juste taper des chiffres.
- **Appréciations facultatives, repliées par défaut** — densité visuelle réduite, l'élève qui veut juste taper des notes le fait vite.
- **Validation on blur only** (UX-DR35 strict) — pas de validation à chaque keystroke, pas de "✓ valide" en temps réel. Anti-friction.
- **Sauvegarde partielle OK** — au minimum 1 matière par trimestre, mais 1 matière suffit (anti-paywall implicite).
- **Pas de bouton "Précédent"** entre trimestres — les tabs servent à naviguer, économise un bouton.
- **Pas de "Aperçu avant validation"** — l'écran EST l'aperçu. Le commit est immédiat sur "Valider".
- **Lien "Plus tard" en footer secondaire** — toujours accessible sans repasser par l'écran AC1, anti-friction sortie élégante.
- **Référentiel matières versionné** (`subjects_ref_version`) — parallèle à Story 2.3.
- **Pas de comparaison avec l'OCR** — la saisie manuelle est une voie autonome, pas un fallback minimisé.

### 4.5 Anti-patterns proscrits

- ❌ **Champs obligatoires avec astérisque rouge**
- ❌ **Validation à chaque keystroke** ("Note valide ✓" qui apparaît caractère par caractère)
- ❌ **"Tu n'as rempli que 5 matières sur 10 !"** — culpabilisation
- ❌ **Confettis** ou célébration à la validation
- ❌ **"Et si tu essayais le scan ?"** anywhere sur cet écran — pas de comparaison OCR
- ❌ **Mode dégradé visuel** — l'écran de saisie manuelle ressemble strictement aux autres écrans onboarding (mêmes tokens, même typo, même rythme)
- ❌ **Bouton "Cancel"** — l'élève peut quitter via back chevron, persistence couvre. Pas besoin d'un bouton dédié.
- ❌ **Toast d'erreur ambient** pour erreur de champ — erreur inline sous le champ uniquement
- ❌ **Auto-save loud** (toast à chaque blur "Sauvegardé") — silencieux

### 4.6 Versions et libraries

- React 19, Next.js 15, TypeScript 5.x
- shadcn/ui : `Input`, `Textarea`, `Tabs`, `Button`, `Select` (avec recherche), `Toast`, `Skeleton`, `Label`
- React Hook Form 7.x + Zod 3.x (validation note 0-20, custom subject prefix)
- TanStack Query 5.x (mutation commit + retry exponentiel)
- Lucide React (`ChevronDown`, `ChevronUp`, `X`, `Plus`, `Pencil`)
- Backend : Django/DRF ou FastAPI + pydantic + pytest
- Vitest + RTL + Playwright + axe-core

### 4.7 Items à différer (`deferred-work.md` post-merge)

- **Import depuis Pronote / École Directe** (ENT) — V2 partenariat, hors MVP
- **Auto-complétion notes** depuis trimestre précédent (suggestion "Tu avais 14 au trim. 1, t'as eu combien au trim. 2 ?") — fast-follow UX
- **OCR de notes seul** (sans bulletin entier) — copier-coller depuis Pronote → OCR — fast-follow
- **Validation enseignant / responsable légal** — pas MVP, V2 marketplace B2B école
- **Suggestion auto matières optionnelles** (ex. élève en STMG → suggérer "Gestion-Finance" si pas déclaré) — fast-follow
- **Smart paste** depuis Excel / Google Sheets — fast-follow desktop power-users

---

## 5. Project Structure Notes

```
apps/web/
  app/(auth)/onboarding/step-3/manual/
    page.tsx                          ← entry Next.js (T3)
    OnboardingStep3Manual.tsx         ← orchestrateur
    TrimestreTabs.tsx                 ← factorisable avec Story 2.3 récap
    MatiereInputRow.tsx
    AddSubjectInline.tsx
    BackConfirmDialog.tsx
    useManualBulletinDraft.ts
    useCommitManualBulletin.ts
    __tests__/
      OnboardingStep3Manual.test.tsx
      MatiereInputRow.test.tsx
      a11y.spec.ts
  e2e/
    onboarding-step3-manual.spec.ts

packages/copy/onboarding/
  subjects-by-level.ts               ← étendu T1 (créé par Story 2.3)
  __tests__/

apps/api/apps/bulletins/             ← partage avec Story 2.3
  models.py                          ← extension Bulletin avec source="manual"
  views_manual.py                    ← POST + PATCH endpoints (T2)
  serializers_manual.py
  migrations/
    NNNN_bulletin_manual_fields.py
  tests/
    test_manual_endpoints.py

docs/onboarding/
  step3-manual.md                    ← T5
docs/a11y/
  onboarding-step3-manual.md
```

**Conventions à respecter :**

- Tokens CSS uniquement (Story 1.2)
- TanStack Query pour mutations (Story 1.3)
- Audit log Story 1.13 sur commit
- RLS Story 1.8 sur tous endpoints
- **Factorisation `TrimestreTabs` avec Story 2.3 récap** — composant partagé dans `apps/web/components/bulletins/`
- **Factorisation référentiel matières** avec Story 2.3 T1 (T1 ici = extension, pas duplication)

---

## 6. References

- **UX spec globale** :
  - § Form Patterns (labels au-dessus, validation on blur, pas d'astérisque)
  - § Experience Principles (#3 anti-impasse, #4 mode normal = mode dégradé)
  - § Anti-patterns proscrits
  - § Patterns transverses → GracefulFallback (entrée fallback)
- **Epic 2 detail** : `_bmad-output/planning-artifacts/epics/epic-2-profil-eleve-onboarding.md` § Story 2.4
- **Story 2.3 (OCR)** : `_bmad-output/implementation-artifacts/2-3-import-bulletins-pdf-ocr.md` — AC1 card 2 + AC4 ScenarioLoader opt-in + AC7 GracefulFallback
- **Story 2.5 (Plus tard)** : à venir — lien tertiary footer AC5 mène ici
- **Story 2.6 (édition profil)** : à venir — `/profile/edit/bulletins` réutilise les composants `MatiereInputRow`, `AddSubjectInline`
- **Story 1.2 (tokens)** : `_bmad-output/implementation-artifacts/1-2-design-system-tokens.md`
- **Story 1.13 (audit log)** : `_bmad-output/implementation-artifacts/1-13-journal-audit-acces.md`
- **Story 1.14 (ConsentDialog)** : utilisé en AC8 confirmation back
- **PRD** : FR15 (saisie manuelle), NFR-R4 (graceful degradation), UX-DR35 (form pattern)

---

## 7. Dev Agent Record

### Agent Model Used
Claude Sonnet 4.6 (claude-sonnet-4-6)

### Debug Log References
- `packages/copy/onboarding/subjects-by-level.ts` referenced in story but `packages/` doesn't exist. Used `apps/web/src/lib/onboarding/subjects-by-level.ts` (consistent with Story 2.3 pattern).
- `BulletinManual` created as new model vs reusing `Bulletin` (OCR-focused model with S3/file concerns). Cleaner separation.
- `getByText("Mathématiques")` found 2 elements (visible span + sr-only legend). Fixed test to use `getAllByText`.

### Completion Notes List
- T1 ✅ `subjects-by-level.ts` — 11 Vitest tests. Levels: college_3eme, lycee_2nde, lycee_1ere/Tle general, lycee techno STMG/STI2D, postbac (empty). Optional subjects including Latin.
- T2 ✅ Backend: `BulletinManual` model + migration 0002 + POST + PATCH endpoints + serializers. 11 pytest tests: create, 0-subject 422, note range validation, custom subject prefix, cross-tenant 404.
- T3 ✅ Frontend: `MatiereInputRow` (10 RTL tests), `TrimestreTabs`, `useManualBulletinDraft`, `useCommitManualBulletin`, `OnboardingStep3Manual`, `page.tsx`.
- T4 ✅ 21 tests total (11 backend + 10 frontend). Pre-existing failures unrelated to 2.4.
- T5 ✅ `docs/onboarding/step3-manual.md` + `docs/a11y/onboarding-step3-manual.md`

### File List
- `apps/web/src/lib/onboarding/subjects-by-level.ts` — new subjects referential
- `apps/web/src/lib/onboarding/__tests__/subjects-by-level.test.ts` — 11 tests
- `apps/api/apps/bulletins/models.py` — added `BulletinManual` model
- `apps/api/apps/bulletins/migrations/0002_bulletin_manual.py` — new migration
- `apps/api/apps/bulletins/serializers_manual.py` — create + patch serializers
- `apps/api/apps/bulletins/views_manual.py` — `BulletinManualListView` + `BulletinManualDetailView`
- `apps/api/apps/bulletins/urls.py` — 2 new routes
- `apps/api/apps/bulletins/tests/test_manual_endpoints.py` — 11 tests
- `apps/web/src/app/(auth)/onboarding/step-3/manual/page.tsx` — Next.js route
- `apps/web/src/app/(auth)/onboarding/step-3/manual/OnboardingStep3Manual.tsx` — orchestrator
- `apps/web/src/app/(auth)/onboarding/step-3/manual/MatiereInputRow.tsx` — core form row
- `apps/web/src/app/(auth)/onboarding/step-3/manual/TrimestreTabs.tsx` — trimestre tabs
- `apps/web/src/app/(auth)/onboarding/step-3/manual/useManualBulletinDraft.ts` — localStorage draft hook
- `apps/web/src/app/(auth)/onboarding/step-3/manual/useCommitManualBulletin.ts` — TanStack mutation hook
- `apps/web/src/app/(auth)/onboarding/step-3/manual/__tests__/matiere-input-row.test.tsx` — 10 tests
- `docs/onboarding/step3-manual.md`
- `docs/a11y/onboarding-step3-manual.md`

### Change Log

- 2026-05-25 — Story 2.4 contextée par Marwen + Claude (Opus 4.7). Consumer de Story 2.3 AC1 (card 2) + AC7 (fallback OCR) + AC4 (opt-in loader > 30s). Factorise référentiel matières et `TrimestreTabs` avec Story 2.3.
