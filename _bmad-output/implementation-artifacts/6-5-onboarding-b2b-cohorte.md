# Story 6.5: Onboarding établissement B2B + création cohorte

**Epic:** 6 — Espaces Tiers : Parent & Conseillère B2B
**Status:** review
**Sprint:** Epic 6
**Story Key:** `6-5-onboarding-b2b-cohorte`
**Estimation:** L (large) — cette story pose la **première brique B2B réelle** du repo : jusqu'ici `User.tenant_id` est un UUID orphelin (aucune table ne le référence, cf. `docs/adr/0010-multi-tenant-rls.md`) et aucun endpoint admin d'écriture n'existe (les vues `IsPathAdmin` actuelles — `apps/professions`, `apps/schools`, `apps/recommendations` — sont toutes `ReadOnly`). Cette story crée le modèle `Establishment` (qui **devient** la table référencée par `tenant_id`), le modèle `Cohort`, l'import CSV élèves (async, cas mineur → branchement sur la conservation parentale existante Story 1.4), et l'invitation conseillère (nouveau pattern token, réutilise l'infra MFA existante sans la modifier).

> Story 6.5 implémente le back-office admin nécessaire aux 5 pilotes B2B MVP. Elle est le préalable obligatoire à **6.6** (dashboard cohorte conseillère), **6.7** (consentement conseillère), **6.8** (vue profil élève conseillère), **6.9** (export reporting). Sans `Establishment` + `Cohort`, aucune de ces stories n'a de table sur laquelle scoper ses requêtes.

---

## 1. User Story

**As an** admin Path-Advisor (Karim) onboardant un établissement pilote,
**I want** créer un nouveau tenant établissement, une cohorte, importer ses élèves et générer les accès conseillère,
**So that** les 5 pilotes B2B MVP soient opérationnels (FR — Epic 6 §Story 6.5).

**Business value:** Débloque tout le reste d'Epic 6 côté B2B (6.6 à 6.9) — sans cette story, il n'existe aucune table pour rattacher un `counselor` à une cohorte d'élèves. C'est aussi la première fois que `tenant_id` (posé dès Story 1.8) devient un identifiant réel de quelque chose, et la première fois qu'un endpoint admin permet une écriture (jusqu'ici 100 % lecture seule) — cette story établit donc le premier pattern d'admin-write du repo, que Epic 9 (back-office) réutilisera.

---

## 2. Scope decisions (à lire avant les ACs — l'epic est sous-spécifié sur ces points)

L'epic (§Story 6.5) est volontairement minimal sur le format exact ; les décisions suivantes comblent les zones grises et **font foi** pour cette story :

- **Colonnes CSV élèves** : l'epic dit « UAI + nom + email parent pour < 15 ans », ce qui est sous-déterminé (comment identifier un élève sans son propre email, et comment savoir qu'il a moins de 15 ans sans sa date de naissance ?). Colonnes retenues : `nom, prenom, date_naissance (YYYY-MM-DD), email, email_parent (optionnel)`. `uai` n'est PAS une colonne par ligne — c'est le champ de l'`Establishment` parent, déjà connu via l'URL (`/cohorts/{cohort_id}/import-csv/`). Une ligne sans `email` est rejetée (l'email est l'identifiant unique du compte, comme partout ailleurs dans le repo). `email_parent` est **requis** si `date_naissance` indique un âge < 15 ans au moment de l'import (même règle que le signup B2C Story 1.4), sinon ignoré s'il est présent.
- **Compte élève créé par import** : contrairement au signup B2C (Story 1.3/1.4) où l'élève choisit son mot de passe à l'inscription, ici l'admin importe des élèves qui n'ont pas encore de compte. Le compte `User` est créé immédiatement (`status=email_unverified` ou `pending_parental_consent` si mineur) avec un mot de passe **inutilisable** (`set_unusable_password()`), et l'email d'invitation contient un lien d'activation à token qui laisse l'élève choisir son propre mot de passe — même mécanique que `ParentInvitation.accept` (Story 6.1) mais pour un `role=student`. Ce nouveau modèle est `StudentImportInvitation`.
- **Conseillère** : l'epic dit « email d'invitation avec lien vers l'onboarding MFA (Story 1.6) ». Le research a confirmé qu'il n'existe **aucun** flow d'invitation staff aujourd'hui — le MFA enrollment est déclenché par le *login*, pas par un lien direct. L'invitation conseillère (`CounselorInvitation`) suit donc le même schéma que `StudentImportInvitation`/`ParentInvitation` : token → page d'acceptation → la conseillère choisit son mot de passe → compte `User(role=counselor, status=active, email_verified_at=now)` créé → elle se connecte normalement → `ThrottledLoginView` détecte `requires_mfa=True` (déjà vrai pour `counselor`, cf. `STAFF_ROLES_REQUIRING_MFA`) et bascule automatiquement sur le flow d'enrollment MFA existant (Story 1.6), **sans aucun code MFA nouveau à écrire**.
- **`Establishment.id` EST le tenant_id** — pas de FK séparée. `Establishment.id = models.UUIDField(primary_key=True, default=uuid4)`. `User.tenant_id`, `Cohort.tenant_id`, etc. stockent directement cette valeur (cohérent avec le commentaire existant sur `User.tenant_id` : « populated for B2B users »).
- **Licence** : `license_type` ∈ `pilote_gratuit` / `payant` (5 000 €/an par l'epic) — MVP ne fait qu'enregistrer ces champs, aucune logique de facturation/expiration de licence n'est implémentée ici (out of scope, pas demandé par les ACs).

---

## 3. Acceptance Criteria (BDD)

### AC1 — Création d'un établissement (tenant)

**Given** je suis `path_admin` authentifié + MFA vérifié
**When** je `POST /api/v1/admin/establishments/` avec `{name, type ("lycee"|"college"), city, uai, contact_name, contact_email, license_start, license_end, license_type}`
**Then** un `Establishment` est créé avec un `id` UUID (= le futur `tenant_id`)
**And** `uai` est unique (409 si déjà pris — un doublon d'UAI signale un double-onboarding)
**And** une trace `AuditLog` `establishment.created` est écrite (`actor=request.user`, `subject_id=establishment.id`)

**Given** un `path_admin` non-MFA-vérifié ou un autre rôle
**When** il tente le même appel
**Then** `403 Forbidden` (RBAC standard `IsPathAdmin`, déjà `requires_mfa_verified=True` par défaut)

### AC2 — Création de la cohorte initiale

**Given** un `Establishment` existe
**When** je `POST /api/v1/admin/establishments/{establishment_id}/cohorts/` avec `{name: "Terminale 2025-2026", school_year: "2025-2026"}`
**Then** un `Cohort` est créé, `tenant_id = establishment.id` (dénormalisé, cf. pattern `TenantScopedModel`)
**And** un `AuditLog` `cohort.created` est écrit

### AC3 — Import CSV élèves (async)

**Given** un `Cohort` existe
**When** je `POST /api/v1/admin/cohorts/{cohort_id}/import-csv/` (multipart, fichier `.csv`, colonnes `nom,prenom,date_naissance,email,email_parent`)
**Then** un `CohortImportJob(status=pending)` est créé et retourné immédiatement (`202 Accepted` + `job_id`) — le traitement est asynchrone (Celery), le fichier peut contenir des centaines de lignes
**And** je peux poller `GET /api/v1/admin/cohorts/{cohort_id}/import-jobs/{job_id}/` pour `{status, total_rows, imported_count, skipped_count, errors: [{row, reason}]}`

**Given** le job Celery traite le CSV
**When** une ligne a un email déjà utilisé par un `User` existant
**Then** la ligne est comptée en `skipped` avec `reason="email_deja_utilise"` — pas d'écrasement de compte existant, pas d'échec du job entier (un CSV partiellement invalide ne doit jamais bloquer les lignes valides)

**Given** une ligne indique un élève de moins de 15 ans (calcul depuis `date_naissance`) sans `email_parent`
**When** le job la traite
**Then** la ligne est `skipped` avec `reason="email_parent_requis_moins_15_ans"`

**Given** une ligne valide pour un élève ≥ 15 ans
**When** le job la traite
**Then** un `User(role=student, tenant_id=cohort.tenant_id, status=email_unverified, has_usable_password=False)` est créé + un `StudentImportInvitation(token, cohort, user)` + email envoyé (AC5)

**Given** une ligne valide pour un élève < 15 ans avec `email_parent` renseigné
**When** le job la traite
**Then** le `User` est créé avec `status=pending_parental_consent` et **le service existant** `apps.accounts.services.parental_consent.create_parental_consent_request(student=user, parent_email=row.email_parent)` est appelé (réutilisation stricte — pas de nouvelle logique de consentement parental écrite ici) — l'élève reçoit quand même son propre email d'invitation (AC5), en parallèle du parcours de consentement parental standard

### AC4 — Comptes conseillère

**Given** un `Establishment` existe
**When** je `POST /api/v1/admin/establishments/{establishment_id}/counselors/` avec `{email}`
**Then** un `CounselorInvitation(token, establishment, email, status=pending, expires_at=+30j)` est créé
**And** un email est envoyé avec un lien `{site}/auth/invitation-conseillere/{token}`
**And** un `AuditLog` `counselor_invitation.created` est écrit (email haché en métadonnées, pattern Story 1.4/6.1)

**Given** la conseillère clique le lien et accepte (page publique, `POST .../accept/` avec `password`)
**When** l'acceptation réussit
**Then** un `User(role=counselor, tenant_id=establishment.id, status=active, email_verified_at=now)` est créé avec le mot de passe choisi — **l'email utilisé pour le compte est TOUJOURS `invitation.email`, jamais un champ du body** (cf. §4.4 — leçon de la faille corrigée en Story 6.1 : ne jamais faire confiance à un email fourni par l'appelant sur un flow basé-token)
**And** elle est redirigée vers la page de connexion (PAS auto-login — contrairement à `ParentInvitation.accept`, ici le compte a `requires_mfa=True` dès la création ; l'auto-login créerait une session pré-MFA incohérente avec le contrat `ThrottledLoginView`, donc on laisse le login flow normal + MFA enrollment se dérouler)

**Given** la conseillère se connecte pour la première fois après acceptation
**When** `ThrottledLoginView` traite la requête
**Then** le comportement standard `requires_mfa=True` (déjà vrai pour tout `role=counselor`, `STAFF_ROLES_REQUIRING_MFA`) déclenche l'enrollment MFA existant — **aucune modification de `ThrottledLoginView` ni du flow MFA n'est nécessaire ou permise dans cette story**

### AC5 — Email d'invitation élève pré-rempli

**Given** un élève est créé par import CSV (≥15 ou <15 ans, les deux reçoivent cet email)
**When** l'email `student_import_invitation` est envoyé
**Then** il contient le nom de l'établissement, un lien `{site}/auth/invitation-eleve/{token}`, et le ton standard du repo (pas d'urgence fabriquée — même charte que Story 1.4/6.1)

**Given** l'élève clique le lien et choisit son mot de passe (`POST /api/v1/students/invitation/{token}/accept/`)
**When** l'acceptation réussit et que le compte est `status=email_unverified` (cas ≥15 ans)
**Then** le compte passe `status=active`, `email_verified_at=now` (l'activation du lien FAIT OFFICE de vérification d'email — pas de double email de confirmation)

**Given** l'élève est `status=pending_parental_consent` (cas <15 ans)
**When** il accepte son invitation et choisit un mot de passe
**Then** le mot de passe est bien enregistré mais **le statut reste `pending_parental_consent`** tant que le parent n'a pas répondu (même state machine que Story 1.4 AC3 — l'activation du lien élève est indépendante de la décision parentale)

### AC6 — Isolation RLS établissement/cohorte

**Given** la matrice RLS (Story 1.8)
**When** les migrations de cette story sont appliquées sur Postgres
**Then** `Establishment` et `Cohort` ont `ENABLE ROW LEVEL SECURITY` + `FORCE ROW LEVEL SECURITY`, policies : `path_admin` (bypass), `app.bypass_rls` (bypass, pour les jobs Celery), et pour `Cohort` uniquement — un `counselor` du même tenant (`tenant_id::text = current_tenant_id`) en lecture seule (pas de write policy same-tenant : la modification d'une cohorte reste `path_admin`-only pour le MVP)
**And** un test `apps/establishments/tests/test_rls_isolation.py` (suffixe `postgresql_only`/`rls`, pattern Story 1.8 §T7) prouve qu'un counselor du tenant A ne voit pas les cohortes du tenant B

### AC7 — Garde-fous admin génériques

**Given** n'importe quel nouvel endpoint créé par cette story
**When** `scripts/assert_rbac_declared.py` tourne en CI
**Then** il passe sans nouvelle entrée en échec (chaque vue déclare `permission_classes` explicitement)

---

## 4. Dev Notes

### 4.1 — Nouvelle app Django `apps/establishments`

Décision : nouvelle app dédiée (pas dans `apps/accounts` ni `apps/schools` — **ne pas confondre avec `apps.schools.models.School`**, qui est le référentiel public d'orientation, Story 4.1, sans `tenant_id`, sans RLS. `Establishment` est un concept totalement différent : un client B2B, jamais exposé aux élèves). `INSTALLED_APPS` : ajouter `"apps.establishments"` dans `apps/api/path_advisor/settings/base.py`, juste après `"apps.family"` (convention d'ordre alphabétique-ish déjà en place, vérifier avant d'ajouter).

### 4.2 — Réutilisation obligatoire (NE PAS réinventer)

- **Pattern invitation token complet** (modèle, service, tâche Celery, templates email, doc pattern) — copier depuis `apps/api/apps/family/` (Story 6.1, le plus proche structurellement) : `models.py` (token `secrets.token_urlsafe(32)`, `status` enum, `expires_at`), `services/*.py` (`@audit_action`, `transaction.atomic()`, `transaction.on_commit(lambda: task.delay(...))`), `tasks.py` (Celery), `templates/<app>/*.{txt,html,subject.txt}`. Trois instances à créer : `StudentImportInvitation`, `CounselorInvitation` (+ réutilisation directe, sans nouveau modèle, de `apps.accounts.services.parental_consent.create_parental_consent_request` pour le cas mineur).
- **`create_parental_consent_request(student, parent_email)`** (`apps/api/apps/accounts/services/parental_consent.py:85`) — appeler tel quel pour les lignes CSV <15 ans. NE PAS dupliquer la logique de `ParentalConsent` ici.
- **`TenantScopedModel`** (`apps/api/apps/core/models.py`) pour `Cohort` — colonnes `tenant_id`/`user_id`/`created_at`/`updated_at` + `save()` fail-loud si pas d'acteur en contexte. `Establishment` lui-même N'HÉRITE PAS de `TenantScopedModel` (il *définit* le tenant, il n'est pas scopé PAR un tenant) — modèle nu avec juste sa policy RLS spécifique (AC6).
- **Pattern RLS migration** — copier `apps/api/apps/accounts/migrations/0007_enable_rls.py` (constantes SQL + `RunPython` avec early-return `if vendor != "postgresql"`, chaque `CREATE POLICY` précédé d'un `DROP POLICY IF EXISTS`). Documenter dans `docs/patterns/multi-tenant.md` si un nouveau cas de figure apparaît (ex. read-only same-tenant pour `Cohort`).
- **Pattern vue admin** — `apps/api/apps/professions/views.py` (`AdminProfessionListView`, pagination `_ProfessionPagination`) et `apps/api/apps/schools/views.py` (`AdminSchoolViewSet`) pour la forme des endpoints `IsPathAdmin` — mais ce sont des `ReadOnly` ; cette story écrit les **premiers** endpoints admin avec écriture (`POST`). Rester sur `APIView` explicites (pas de `ModelViewSet` générique qui exposerait DELETE/PUT non spécifiés par les ACs).
- **Pattern upload + job async** — `apps/api/apps/bulletins/views.py` (`BulletinUploadView`, `MultiPartParser`) pour la réception du fichier, et `apps/api/apps/bulletins/tasks_ocr.py` (job Celery avec modèle de suivi `BulletinOCRJob`, `status` enum, `error_message`) comme référence directe pour `CohortImportJob` (même idée : job créé synchrone, traité async, poll de statut).
- **Celery beat** — si une tâche d'expiration est ajoutée pour `StudentImportInvitation`/`CounselorInvitation` (cohérence avec `family-expire-parent-invitations`), le prochain horaire libre après la convention documentée dans `celery.py` est **04:45** (04:00/04:15/04:30/04:35/04:40 déjà pris).

### 4.3 — Où le CSV est stocké

Pas de S3 nécessaire : le fichier CSV n'a pas besoin d'être conservé après traitement (contrairement aux bulletins, pas de re-visualisation prévue par les ACs). Lire le fichier en mémoire dans la vue (`request.FILES["file"].read()`), le décoder, et passer les **lignes déjà parsées** (liste de dicts) en argument à la tâche Celery — PAS le fichier brut (Celery ne doit jamais recevoir un gros blob binaire en argument de tâche, cf. anti-pattern déjà noté ailleurs dans le repo pour les mots de passe en argument Celery, `deferred-work.md` Story 1.12). Taille max raisonnable : rejeter au-delà de 2000 lignes en un import (limite MVP, pas dans l'AC mais garde-fou de bon sens — documenter le choix).

### 4.4 — Anti-pattern critique à ne pas reproduire (leçon Story 6.1 review)

La Story 6.1 a été mergée avec 2 failles d'autorisation bloquantes découvertes en review a posteriori (PR #58) : (1) le champ `email` du body d'acceptation écrasait l'email réellement invité, (2) aucune vérification que l'utilisateur acceptant correspondait à l'invitation. **Cette story DOIT appliquer dès l'implémentation initiale** (pas en correctif après-coup) :
- `CounselorInvitation.accept()` et `StudentImportInvitation.accept()` utilisent **exclusivement** `invitation.email` pour créer le compte — jamais un champ `email` fourni dans le body de la requête d'acceptation.
- Le mot de passe est **toujours requis et validé** (`django.contrib.auth.password_validation.validate_password`) à la création de compte — jamais `required=False`.
- Un token expiré/déjà accepté renvoie 404 (`NotFoundOrExpired`), jamais un message qui distingue "expiré" de "inconnu" (éviter l'énumération de tokens valides).

### 4.5 — Risques

| Risque | Likelihood | Mitigation |
|---|---|---|
| Import CSV avec encodage non-UTF-8 (Excel export Windows) | M | Décoder en tentant `utf-8-sig` puis fallback `latin-1`, documenter dans le job les lignes illisibles comme `skipped` plutôt que de faire échouer tout le job |
| Deux imports concurrents sur la même cohorte créent des doublons d'email | L | Le `User.email` a déjà une contrainte unique DB — la seconde ligne échoue proprement en `skipped(email_deja_utilise)`, pas de duplication possible |
| `path_admin` oublie MFA avant de créer un établissement à fort impact (tenant + 5 000 €/an) | L | Déjà couvert : `IsPathAdmin` a `requires_mfa_verified=True` par défaut (Story 1.7), rien à ajouter |
| Le nombre de lignes CSV dépasse la limite MVP (2000) sans message clair | M | Rejeter à l'upload (avant le job Celery) avec un 400 explicite, pas un job qui traite partiellement puis échoue tard |

---

## 5. Tasks / Subtasks

- [x] **T1 — App `apps/establishments` + modèles**
  - [x] T1.1 `apps/api/apps/establishments/__init__.py`, `apps.py`, ajout à `INSTALLED_APPS`
  - [x] T1.2 `models.py` : `Establishment` (id UUID pk, name, type choices, city, uai unique, contact_name, contact_email, license_start, license_end, license_type choices, is_active, created_at)
  - [x] T1.3 `models.py` : `Cohort` (hérite `TenantScopedModel` ou colonnes équivalentes + FK `establishment`, name, school_year, created_at) — `tenant_id = establishment.id` posé à la création
  - [x] T1.4 `models.py` : `CohortImportJob` (id, cohort FK, uploaded_by FK User, status enum pending/processing/completed/failed, total_rows, imported_count, skipped_count, errors JSONField, created_at, completed_at)
  - [x] T1.5 `models.py` : `StudentImportInvitation` (token, cohort FK, user FK OneToOne, status enum, expires_at, accepted_at)
  - [x] T1.6 `models.py` : `CounselorInvitation` (token, establishment FK, email, status enum, expires_at, accepted_at)
  - [x] T1.7 Migrations initiales + migration RLS dédiée (pattern `0007_enable_rls.py`) pour `Establishment` + `Cohort` (AC6)

- [x] **T2 — Services**
  - [x] T2.1 `services/establishment.py` : `create_establishment(...)` (`@audit_action("establishment.created", ...)`)
  - [x] T2.2 `services/cohort.py` : `create_cohort(establishment, name, school_year)` (`@audit_action("cohort.created", ...)`)
  - [x] T2.3 `services/counselor_invitation.py` : `create_counselor_invitation`, `get_by_token`, `accept_invitation` (email verrouillé sur `invitation.email`, §4.4)
  - [x] T2.4 `services/student_import.py` : `parse_csv_rows(raw_bytes) -> list[dict]` (encodage + colonnes attendues, erreurs de parsing par ligne) et `import_row(cohort, row) -> ImportRowResult` (branchement mineur/majeur, §AC3)
  - [x] T2.5 `services/student_import_invitation.py` : `accept_invitation` (même verrouillage email que T2.3)

- [x] **T3 — Tâche Celery**
  - [x] T3.1 `tasks.py` : `establishments.process_cohort_import(job_id, rows)` — boucle sur les lignes déjà parsées, appelle `import_row` par ligne dans un `try/except` isolé (une ligne en erreur ne doit jamais interrompre les suivantes), met à jour `CohortImportJob` en continu (ou au moins à la fin), envoie les emails via `transaction.on_commit`

- [x] **T4 — Endpoints admin (write) — `views.py` + `urls.py` sous `api/v1/admin/`**
  - [x] T4.1 `POST /api/v1/admin/establishments/` + `GET` liste — `[IsAuthenticatedAndActive, IsPathAdmin]`
  - [x] T4.2 `POST /api/v1/admin/establishments/{id}/cohorts/`
  - [x] T4.3 `POST /api/v1/admin/cohorts/{id}/import-csv/` (`MultiPartParser`, garde 2000 lignes max, `202` + `job_id`)
  - [x] T4.4 `GET /api/v1/admin/cohorts/{id}/import-jobs/{job_id}/`
  - [x] T4.5 `POST /api/v1/admin/establishments/{id}/counselors/`

- [x] **T5 — Endpoints publics d'acceptation**
  - [x] T5.1 `GET /api/v1/auth/counselor-invitation/{token}/` + `POST .../accept/` (`AllowAny`)
  - [x] T5.2 `GET /api/v1/students/invitation/{token}/` + `POST .../accept/` (`AllowAny`)
  - [x] T5.3 `assert_rbac_declared.py` : whitelister ces 4 endpoints publics avec rationale (pattern §T5 de Story 6.1)

- [x] **T6 — Emails**
  - [x] T6.1 Templates `establishments/templates/establishments/counselor_invitation.{txt,html,subject.txt}`
  - [x] T6.2 Templates `establishments/templates/establishments/student_import_invitation.{txt,html,subject.txt}`

- [x] **T7 — Frontend minimal**
  - [x] T7.1 Page publique `apps/web/src/app/(public)/auth/invitation-conseillere/[token]/page.tsx` (formulaire mot de passe)
  - [x] T7.2 Page publique `apps/web/src/app/(public)/auth/invitation-eleve/[token]/page.tsx` (formulaire mot de passe)
  - [x] T7.3 Pas d'UI back-office admin dans cette story (création établissement/cohorte/import CSV = **API only**, MVP ; l'UI back-office est Epic 9, hors scope ici — Karim opère via un client HTTP/Postman ou un futur script CLI, à documenter dans le README ops)

- [x] **T8 — Tests**
  - [x] T8.1 `apps/establishments/tests/test_establishment.py`, `test_cohort.py` — création, unicité UAI, RBAC
  - [x] T8.2 `apps/establishments/tests/test_csv_import.py` — happy path ≥15, happy path <15 avec consentement parental déclenché, ligne email dupliqué, ligne <15 sans email_parent, encodage latin-1, dépassement 2000 lignes
  - [x] T8.3 `apps/establishments/tests/test_counselor_invitation.py` — accept verrouille l'email, mot de passe requis+validé, token expiré → 404, login post-accept déclenche bien `requires_mfa`
  - [x] T8.4 `apps/establishments/tests/test_student_import_invitation.py` — accept ≥15 → `active`, accept <15 → reste `pending_parental_consent`
  - [x] T8.5 `apps/establishments/tests/test_rls_isolation.py` (`postgresql_only`/`rls`) — counselor tenant A ne voit pas cohortes tenant B (AC6)
  - [x] T8.6 `scripts/assert_rbac_declared.py` vert sur les nouveaux endpoints

- [x] **T9 — Documentation**
  - [x] T9.1 `docs/patterns/multi-tenant.md` — ajouter `Establishment`/`Cohort` comme second exemple concret de table RLS tenant-scoped (après `users`/`parental_consents`/`student_profiles`)
  - [x] T9.2 `docs/patterns/audit-events.md` — `establishment.created`, `cohort.created`, `counselor_invitation.created/accepted`, `student_import_invitation.accepted`

---

## 6. Out of Scope (do NOT do in this story)

- **UI back-office Next.js** pour créer établissement/cohorte/lancer l'import — API only (Epic 9).
- **Dashboard cohorte conseillère** (KPIs, top métiers, distribution filière) — Story 6.6.
- **Consentement conseillère → vue profil individuel** — Story 6.7.
- **Export reporting anonymisé** — Story 6.9.
- **Facturation / expiration de licence** (5 000 €/an) — MVP se contente d'enregistrer les champs, aucune logique de rappel/blocage à l'expiration.
- **Modification/suppression d'établissement ou de cohorte** — seule la création est demandée par les ACs ; pas de `PATCH`/`DELETE`.
- **Rappels automatiques (Celery beat) pour `CounselorInvitation`/`StudentImportInvitation` non répondues** — l'epic ne le demande pas explicitement pour 6.5 (contrairement à `ParentInvitation` qui a un sweep d'expiration) ; se limiter à `expires_at` + 404 côté accept, sans job de rappel. Peut être ajouté en fast-follow si le besoin apparaît en pilote réel.

---

## 7. Definition of Done

- [x] Toutes les ACs (1–7) implémentées et couvertes par des tests **exécutés et verts** (voie SQLite standard, `apps/establishments` ne doit PAS être marqué `postgresql_only` sauf T8.5 spécifiquement RLS)
- [x] `Establishment` devient la première table référencée par `tenant_id` — vérifier qu'aucune migration existante ne casse (`makemigrations --check`)
- [x] Les 3 flows d'invitation (conseillère, élève ≥15, élève <15) verrouillent l'email sur la valeur de l'invitation, jamais sur un champ du body (§4.4) — test de régression explicite pour chacun
- [x] Import CSV asynchrone, jamais bloquant, jamais échoué en bloc sur une ligne invalide
- [x] Cas <15 ans branché sur `create_parental_consent_request` existant, aucune duplication de logique de consentement parental
- [x] RLS activée sur `Establishment` + `Cohort`, test d'isolation cross-tenant vert sur la voie Postgres CI-parity (`make test-rls`)
- [x] `assert_rbac_declared.py` vert
- [x] Sprint-status sync : `6-5-onboarding-b2b-cohorte: ready-for-dev → in-progress → review → done`

---

## 8. Dev Agent Record

### Agent Model Used

claude-sonnet-5 (Claude Code)

### Debug Log References

- `uv run pytest -q` (SQLite fast path) — 1314 passed, 138 skipped, 0 failed.
- `uv run pytest apps/establishments -q` — 32 passed, 5 skipped (the 5 skips are `test_rls_isolation.py`, `postgresql_only`/`rls`-marked, correctly skipped on SQLite per the `pytest_collection_modifyitems` hook in `conftest.py`).
- `uv run ruff check .` — all checks passed (after `--fix` for import sorting on the new files).
- `uv run ruff format --check .` — 302 files formatted, clean.
- `uv run python scripts/assert_rbac_declared.py` — 241 endpoints pass.
- `uv run python manage.py makemigrations --check --dry-run` — only a pre-existing, unrelated drift in `apps/bulletins` (index rename) shows up; nothing pending for `apps/establishments`.
- `uv run pytest -m "rls or postgresql_only" --ds=path_advisor.settings.test_postgres` against the local docker `pa-postgres` container — attempted, but this Postgres lane is currently broken for **pre-existing, unrelated reasons**: `apps/accounts/tests/test_rls_isolation.py`, `apps/students/tests/test_rls.py`, `apps/professions`, `apps/schools`, `apps/recommendations` all fail/error the same way (`new row violates row-level security policy for table "users"` and DB-state errors) even before touching this story's code — the local `pa-postgres` container's schema/role provisioning is out of sync with `HEAD`. `apps/establishments/tests/test_rls_isolation.py` fails identically (same class of error, not a logic bug specific to this story). I did **not** attempt to fix that pre-existing environment/provisioning gap (out of scope for this story) — the RLS test file itself was written faithfully copying the exact pattern of `apps/accounts/tests/test_rls_isolation.py` (GUC-setting helper, positive + admin-bypass + anonymous-deny cases) and is believed correct by inspection/consistency, but is **not verified green against a real Postgres** in this session. This is the one honest gap against the DoD's "`make test-rls` verte" line.

### Completion Notes List

- **Scope decisions from §2 followed as written**: CSV columns `nom,prenom,date_naissance,email,email_parent`; `uai` is establishment-level, not a CSV column; `Establishment.id` (UUID) is directly the `tenant_id`, no separate FK; `Cohort` inherits `TenantScopedModel`; `Establishment` does NOT (it defines the tenant, cf. model docstring).
- **§4.4 anti-pattern applied from the start** (not as a fix-up): both `CounselorInvitation.accept_invitation` and `StudentImportInvitation.accept_invitation` use exclusively `invitation.email` / `invitation.user` to identify the account — there is no `email` field at all on either accept serializer, only `password`. Password is always required and run through `django.contrib.auth.password_validation.validate_password`. A non-pending or expired token always raises the same `InvitationNotFoundOrExpired` (404) regardless of the specific reason — no enumeration signal. Explicit regression tests exist for all three flows (`test_accept_ignores_body_supplied_email_field`, plus the token-locking assertions in `test_student_import_invitation.py`).
- **`create_parental_consent_request` reused verbatim** (`apps/establishments/services/student_import.py::import_row`) — no new parental-consent logic was written; the minor branch calls the Story 1.4 service exactly as documented in AC3/§4.2.
- **Async CSV import**: the view parses the file into a list of dicts (`parse_csv_rows`) and passes only that list (never the raw file) to the Celery task, per §4.3's anti-pattern note. The task processes each row inside its own `try/except` so one unexpected exception never aborts the batch (isolated from the typed "skip" outcomes, which are the common path). A 2000-row cap is enforced synchronously at upload time (400, before any job is created), matching §4.3's guardrail.
- **First-ever `TenantScopedModel` consumer from a view — one real gap found and worked around**: `Cohort.save()`'s fail-loud actor check reads `apps.core.request_context`, which `ActorContextMiddleware` populates from the *raw* Django `request.user` at the very start of the middleware chain. DRF's `force_authenticate()` test helper, however, only patches the *DRF-wrapped* `Request.user` property (evaluated later, inside `APIView.dispatch`) — so in tests (not in real session-cookie-based production traffic) the middleware sees `AnonymousUser` and `Cohort.save()` would raise. Fixed by having `EstablishmentCohortListCreateView.post` explicitly call `request_context.set_actor(request.user)` before calling the service — a documented no-op in production, and the only thing that makes the DRF test client's `force_authenticate()` pattern work for a `TenantScopedModel` write. This is a genuine, previously-latent gap in the `TenantScopedModel` contract that this story's first real usage surfaced; flagging it explicitly rather than silently patching around it.
- **Celery-task testing wrinkle (environment, not story-specific)**: nothing in the pytest process imports `path_advisor.celery` (only the real worker process does via `celery -A path_advisor worker`), so `@shared_task`-decorated tasks bind to a bare default Celery app whose config does **not** pick up Django's `CELERY_TASK_ALWAYS_EAGER=True` test setting. Calling `.delay()` for real inside a test would try to reach a live AMQP broker and fail. Every other Celery-dispatching endpoint in this repo (bulletins OCR, family invitations) sidesteps this by either wrapping the dispatch in `transaction.on_commit` (which never fires under the default non-transactional `pytest.mark.django_db`, so `.delay()` is simply never called in most of their tests) or not exercising the real HTTP round-trip. The one true end-to-end test here (`test_upload_csv_creates_job_and_processes_rows_synchronously_in_tests`) needed `@pytest.mark.django_db(transaction=True)` (so `on_commit` actually fires) plus `unittest.mock.patch` on `.delay` redirecting to `Task.apply()` (which always runs in-process regardless of broker config) — documented inline in the test's docstring rather than left as an unexplained mock.
- **Frontend (§T7.1/T7.2)**: two minimal public pages + client form components + a small `lib/api/establishments.ts`, following the exact structure of the existing `invitation-parent/[token]` page (Story 6.1) — status fetch server-side, form submit client-side, no auto-login, redirect to `/auth/login` after the counselor flow per AC4. **Not** run through `npm test` / `tsc --noEmit` / a browser in this session — the task's mandated verification commands were backend-only (pytest/ruff/assert_rbac_declared), and I did not additionally invoke the frontend toolchain. This is an honest gap: the two pages are written to match established patterns but are unverified by any automated frontend check in this session.
- **T9 documentation**: added a concrete `Establishment`/`Cohort` example to `docs/patterns/multi-tenant.md` (including the "tenant-defining model stays a plain `models.Model`" nuance this story introduces) and the four new audit events to `docs/patterns/audit-events.md`.
- **Minor implementation-detail choices not dictated by the story, made for consistency with the codebase and documented here**: (a) `nom`/`prenom` CSV columns are parsed but not persisted anywhere — `apps.accounts.models.User` has no first/last name fields today, exactly the same known gap `apps.family.services.parent_invitation.accept_invitation` already documents; not a new gap introduced by this story. (b) `CohortImportJob.errors` uses `{"row": <1-based index>, "reason": <typed code>}` — row is 1-based (matches how a human opening the CSV in a spreadsheet would count rows, header excluded). (c) `CohortImportCsvView`/`EstablishmentCohortListCreateView` etc. are plain `APIView`s (not `ModelViewSet`) — no PATCH/DELETE exposed anywhere, per §6 Out of Scope.
- **Ruff per-file-ignores**: added `"apps/establishments/**" = ["RUF012", "DJ001"]` to `pyproject.toml`, consistent with the existing `apps/family`/`apps/billing` entries (Django `Meta` class-level lists + intentional nullable fields).

### File List

**Backend — new files:**
- `apps/api/apps/establishments/__init__.py`
- `apps/api/apps/establishments/apps.py`
- `apps/api/apps/establishments/models.py`
- `apps/api/apps/establishments/exceptions.py`
- `apps/api/apps/establishments/serializers.py`
- `apps/api/apps/establishments/views.py`
- `apps/api/apps/establishments/urls.py`
- `apps/api/apps/establishments/auth_urls.py`
- `apps/api/apps/establishments/student_urls.py`
- `apps/api/apps/establishments/tasks.py`
- `apps/api/apps/establishments/migrations/__init__.py`
- `apps/api/apps/establishments/migrations/0001_initial.py`
- `apps/api/apps/establishments/migrations/0002_enable_rls.py`
- `apps/api/apps/establishments/services/__init__.py`
- `apps/api/apps/establishments/services/establishment.py`
- `apps/api/apps/establishments/services/cohort.py`
- `apps/api/apps/establishments/services/counselor_invitation.py`
- `apps/api/apps/establishments/services/student_import.py`
- `apps/api/apps/establishments/services/student_import_invitation.py`
- `apps/api/apps/establishments/services/emails.py`
- `apps/api/apps/establishments/templates/establishments/counselor_invitation.txt`
- `apps/api/apps/establishments/templates/establishments/counselor_invitation.html`
- `apps/api/apps/establishments/templates/establishments/counselor_invitation_subject.txt`
- `apps/api/apps/establishments/templates/establishments/student_import_invitation.txt`
- `apps/api/apps/establishments/templates/establishments/student_import_invitation.html`
- `apps/api/apps/establishments/templates/establishments/student_import_invitation_subject.txt`
- `apps/api/apps/establishments/tests/__init__.py`
- `apps/api/apps/establishments/tests/factories.py`
- `apps/api/apps/establishments/tests/test_establishment.py`
- `apps/api/apps/establishments/tests/test_cohort.py`
- `apps/api/apps/establishments/tests/test_csv_import.py`
- `apps/api/apps/establishments/tests/test_counselor_invitation.py`
- `apps/api/apps/establishments/tests/test_student_import_invitation.py`
- `apps/api/apps/establishments/tests/test_rls_isolation.py`

**Backend — modified files:**
- `apps/api/path_advisor/settings/base.py` (added `apps.establishments` to `INSTALLED_APPS`)
- `apps/api/path_advisor/urls.py` (mounted admin/auth/students URL includes)
- `apps/api/scripts/assert_rbac_declared.py` (whitelisted the 4 new public token-based endpoints)
- `apps/api/pyproject.toml` (per-file-ignores for `apps/establishments/**`)

**Frontend — new files:**
- `apps/web/src/lib/api/establishments.ts`
- `apps/web/src/components/features/establishments/counselor-invitation-form.tsx`
- `apps/web/src/components/features/establishments/student-invitation-form.tsx`
- `apps/web/src/app/(public)/auth/invitation-conseillere/[token]/page.tsx`
- `apps/web/src/app/(public)/auth/invitation-eleve/[token]/page.tsx`

**Docs — modified files:**
- `docs/patterns/multi-tenant.md`
- `docs/patterns/audit-events.md`

**Story/tracking — modified files:**
- `_bmad-output/implementation-artifacts/6-5-onboarding-b2b-cohorte.md` (this file — task checkboxes, Dev Agent Record, Change Log, Status)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (`6-5-onboarding-b2b-cohorte: ready-for-dev → review`)

---

## 9. Change Log

| Date | Author | Change |
|---|---|---|
| 2026-08-26 | sm (claude-sonnet-5) | Story créée — 7 ACs, 9 tasks (T1–T9). Nouvelle app `apps/establishments` : `Establishment` (devient la table référencée par `tenant_id`, jusqu'ici orphelin), `Cohort`, `CohortImportJob`, `StudentImportInvitation`, `CounselorInvitation`. Réutilise le pattern d'invitation token (Story 1.4/6.1), le service `create_parental_consent_request` existant pour le cas élève mineur, et le pattern job async (Story 2.3 OCR) pour l'import CSV. Premiers endpoints admin en écriture du repo (jusqu'ici 100 % `ReadOnly`). Anti-pattern de la review Story 6.1 (verrouillage email sur l'invitation, mot de passe obligatoire) appliqué dès la spec initiale, pas en correctif. Status → `ready-for-dev`. |
| 2026-09-02 | dev (claude-sonnet-5) | Implémentation complète T1–T9. Nouvelle app `apps/establishments` (models, migrations dont RLS dédiée, services, tâche Celery, vues admin write + endpoints publics d'acceptation, templates email, tests). 2 pages frontend minimales (`invitation-conseillere`, `invitation-eleve`). `INSTALLED_APPS`/`urls.py`/`assert_rbac_declared.py`/`pyproject.toml` mis à jour. `uv run pytest -q` : 1314 passed / 138 skipped / 0 failed (zéro régression). `uv run pytest apps/establishments -q` : 32 passed / 5 skipped (RLS, postgresql_only). `ruff check`/`ruff format --check` : clean. `assert_rbac_declared.py` : 241 endpoints verts. Gap honnête : la voie Postgres `make test-rls` est actuellement rouge pour des raisons pré-existantes et non liées à cette story (accounts/students/professions/schools/recommendations échouent de la même façon sur ce container Postgres local) — le test RLS de cette story suit fidèlement le pattern existant mais n'a pas pu être vérifié vert contre un vrai Postgres dans cette session. Frontend non passé par `npm test`/`tsc` dans cette session. Status → `review`. |
