# Story 1.3 : Inscription élève ≥ 15 ans avec consentement RGPD direct

**Epic :** 1 — Foundation : Auth multi-rôle, RBAC, Conformité RGPD & Infra technique
**Status :** done
**Sprint :** 1 (Fondations)
**Story Key :** `1-3-inscription-eleve-15-ans-rgpd`
**Estimation :** L (large) — premier vrai feature : crée `apps/accounts/` Django + User model custom + signup flow + GDPR policy page. Tous les patterns d'auth posés ici seront réutilisés par Stories 1.4 (parental), 1.5 (login), 1.6 (MFA), 1.7 (RBAC).

> Story 1.3 = première rencontre du front et du back en mode "vraie feature". Pose le User model, l'auth via `django-allauth` + `dj-rest-auth`, le pattern session cookie + CSRF cross-origin, le pattern email transactionnel via Mailpit, et la page de politique RGPD légalement conforme.

---

## 1. User Story

**As a** lycéen ≥ 15 ans (persona Sarah, Terminale),
**I want** créer mon compte avec mon email et mon mot de passe, en acceptant les CGU et la politique RGPD,
**So that** je peux accéder à Path-Advisor sans intervention parentale tout en étant pleinement informé de mes droits.

**Valeur métier :** porte d'entrée du produit pour la moitié de la cible MVP (lycéens 15-18 ans, persona Sarah). Bloque toutes les stories suivantes qui supposent un utilisateur authentifié (Stories 1.4-1.14, Epic 2-10). Le pattern auth posé ici (session cookie + CSRF + `apiFetch`) deviendra **la convention canonique** du projet.

---

## 2. Acceptance Criteria (BDD)

### AC1 — Inscription minimale (email + password + birthdate + consent)

**Given** je suis sur `/auth/signup` et je saisis : email valide, mot de passe (≥ 12 caractères, Django validators), date de naissance impliquant `age ≥ 15`
**When** je clique sur "Créer mon compte" SANS cocher la case de consentement RGPD
**Then** le bouton est **disabled** (ou la validation form-level échoue) avec un message clair "Tu dois accepter les CGU et la politique RGPD pour continuer" — pas d'erreur générique navigateur.

**Given** je coche la case "J'accepte les CGU et la politique RGPD" (avec lien `/legal/rgpd` visible et focusable)
**When** je clique sur "Créer mon compte"
**Then** un compte est créé en base avec :
- `role = student`
- `status = email_unverified`
- `birth_date` enregistrée
- `consent_rgpd_at` = timestamp UTC immuable
- `consent_cgu_version` = version actuelle (ex. `"2026-05-15"` — string YYYY-MM-DD)

**And** un email de vérification d'adresse est envoyé via Mailpit en local (port 1025) ou Postmark en prod (selon `DJANGO_SETTINGS_MODULE`)
**And** la réponse API `POST /api/v1/auth/registration/` retourne `201 Created` avec corps `{"detail": "Verification e-mail sent."}` (snake_case)
**And** une session cookie httpOnly SameSite=Lax est posée *(le front reste sur la page "Vérifie tes emails" — pas de redirect immédiat tant que l'email n'est pas vérifié)*

### AC2 — Validation âge ≥ 15 ans

**Given** je saisis une date de naissance impliquant `age < 15` (e.g. moins de 15 ans révolus à la date d'aujourd'hui)
**When** je clique sur "Créer mon compte"
**Then** la validation backend rejette avec `400 Bad Request` + format RFC 7807 (`type=https://path-advisor.fr/errors/age-under-15`, `title="Inscription mineur sous 15 ans"`, `status=400`, `detail="L'inscription des moins de 15 ans nécessite un consentement parental — flow disponible prochainement (Story 1.4)."`)
**And** côté front, le formulaire affiche le `detail` du Problem inline (au lieu du toast générique) avec un lien "En savoir plus" vers `/legal/rgpd#mineurs`.

> Note : la VRAIE inscription < 15 ans (avec opt-in parental email) sera Story 1.4. Ici on rejette proprement avec un message intentionnellement explicite.

### AC3 — Email de vérification

**Given** un compte vient d'être créé en `email_unverified`
**When** je consulte mon inbox (Mailpit local : `http://localhost:8025`)
**Then** je trouve un email :
- **From** : `no-reply@path-advisor.local`
- **Subject** : "Vérifie ton adresse email pour démarrer sur Path-Advisor"
- **Corps** : un lien unique au format `https://localhost:3000/auth/verify-email?key=<token>` où `<token>` est généré par `allauth.account.models.EmailConfirmationHMAC`
- **Token TTL** : 3 jours (settings `ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 3`)

**And** le contenu est en français, ton aligné avec les principes UX (pas d'urgence fabriquée, voix complice — cf. §4.6 micro-copy)
**And** un lien `mailto:dpo@path-advisor.fr` est mentionné en pied d'email

### AC4 — Click sur le lien → activation

**Given** je clique sur le lien de vérification reçu (token valide, non expiré)
**When** Next.js charge `/auth/verify-email?key=<token>`
**Then** la page appelle `POST /api/v1/auth/registration/verify-email/` avec `{"key": "<token>"}`
**And** le compte passe de `email_unverified` → `active` (champ `email_verified_at = now()`)
**And** la session cookie reste valide (l'utilisateur est désormais authentifié pleinement)
**And** Next.js redirige vers `/onboarding` (placeholder route — l'onboarding réel est Epic 2 Story 2.1)

**Given** je clique sur un lien expiré (> 3 jours) ou déjà utilisé
**When** Next.js appelle l'API
**Then** la réponse est `400` + Problem Details `type=https://path-advisor.fr/errors/email-token-invalid`
**And** la page affiche un état "Lien expiré ou déjà utilisé" avec un CTA "Renvoyer un email" qui appelle `POST /api/v1/auth/registration/resend-email/`

### AC5 — Politique RGPD légalement conforme

**Given** je suis sur `/legal/rgpd` (route publique, accessible sans login)
**When** je consulte la page
**Then** elle contient au minimum les **8 sections obligatoires** :

1. **Responsable du traitement** : Path-Advisor (raison sociale TBD, adresse postale TBD — utiliser placeholders `[À DÉFINIR avant production]` pour MVP local)
2. **Finalités du traitement** :
   - Fournir le service d'orientation (recommandation vocationnelle + graphe parcours)
   - Communication transactionnelle (vérification email, notifications)
   - Amélioration produit (analytics anonymisé via PostHog opt-in)
3. **Base légale** :
   - Consentement explicite (signup + cases à cocher)
   - Exécution contractuelle (CGU)
4. **Catégories de données collectées** : email, mot de passe haché, date de naissance, profil scolaire (bulletins, passions, intérêts, valeurs — Epic 2), interactions produit
5. **Durée de conservation** :
   - Compte actif : indéfiniment tant que l'utilisateur ne se désinscrit pas
   - Compte inactif > 24 mois : email d'avertissement puis purge sous 30 jours (à confirmer DPO)
   - Audit log : 3 ans pseudonymisé (NFR-S4)
6. **Mes droits RGPD** : accès, rectification, portabilité (FR10), suppression / droit à l'oubli (FR11), opposition, limitation
7. **DPO** : `dpo@path-advisor.fr` (mutualisé externe — placeholder pour MVP)
8. **Autorité de contrôle** : CNIL — adresse postale + lien `https://www.cnil.fr/fr/plaintes`

**And** la page est en français, accessible RGAA AA (hierarchie h1>h2>h3 propre, lien CNIL externe avec `rel="noopener"`, contraste ≥ 4.5:1).
**And** une ancre `#mineurs` cible la section "Inscription des < 15 ans" pour le deep-link depuis le message d'erreur AC2.
**And** la page est SSR (`export const dynamic = "force-static"`) — chargement < 1s sur 3G mobile.

### AC6 — Sécurité : rate limiting + password validators

**Given** des tentatives répétées de signup depuis la même IP
**When** plus de **5 signups en 1 heure** depuis cette IP
**Then** la 6e tentative renvoie `429 Too Many Requests` + Retry-After header. Implémenté via `django-ratelimit` (ou cache Redis manuel si plus simple en MVP).

**Given** Django password validators standards (UserAttributeSimilarity, MinLength=12, CommonPassword, Numeric)
**When** je saisis un mot de passe non conforme (e.g. `"password"`, ou `"123456789012"`)
**Then** la réponse est `400` + Problem Details listant **toutes** les violations dans `errors[]` (pas une seule à la fois). Le front affiche chaque erreur sous le champ password.

### AC7 — Tests automatisés couvrant le happy path et 5 cas d'erreur

**Given** la story implémentée
**When** je lance `make test`
**Then** les tests pytest couvrent au minimum :

1. **Happy path** : signup ≥ 15 ans avec consent → 201 + user créé + email envoyé (via `locmem` email backend en test)
2. **Refus consent** : signup sans `consent_rgpd_accepted=true` → 400 RFC 7807
3. **Age < 15** : signup avec birthdate il y a 10 ans → 400 + `type=age-under-15`
4. **Email déjà utilisé** : signup 2e fois avec même email → 400 + `type=email-already-registered` (sans révéler si l'email existe — message générique côté API public, message précis loggué côté serveur)
5. **Password faible** : signup avec password `"12345678"` → 400 + violations dans `errors[]`
6. **Verify email happy path** : appel `verify-email` avec token valide → 200 + statut user passe `active`
7. **Rate limit** : 6e tentative signup → 429 (skip si trop lourd à mocker — acceptable de tester via factory_boy timing)

**And** Vitest côté front teste : composant `SignupForm` (rend les 4 inputs + checkbox + bouton ; valide age < 15 côté client ; affiche les erreurs API en français).

---

## 3. Tasks / Subtasks

### T1 — Câbler `django-allauth` + `dj-rest-auth` + custom User (AC1-AC2)

- [x] T1.1 Mettre à jour `apps/api/path_advisor/settings/base.py` :
  - `INSTALLED_APPS` += `"allauth"`, `"allauth.account"`, `"allauth.socialaccount"` (requis par allauth even sans social), `"dj_rest_auth"`, `"dj_rest_auth.registration"`, `"apps.accounts"`
  - `MIDDLEWARE` += `"allauth.account.middleware.AccountMiddleware"` (requis allauth 0.55+)
  - `AUTH_USER_MODEL = "accounts.User"` *(à set AVANT toute migration ; voir §4.5 reset DB)*
  - Bloc `ACCOUNT_*` allauth : `ACCOUNT_LOGIN_METHODS = {"email"}`, `ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]`, `ACCOUNT_EMAIL_VERIFICATION = "mandatory"`, `ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 3`, `ACCOUNT_USER_MODEL_USERNAME_FIELD = None`, `ACCOUNT_UNIQUE_EMAIL = True`, `ACCOUNT_ADAPTER = "apps.accounts.adapters.PathAdvisorAccountAdapter"` (créé en T1.4)
  - Bloc `REST_AUTH` : `REGISTER_SERIALIZER = "apps.accounts.serializers.SignupSerializer"`, `SESSION_LOGIN = True`, `USE_JWT = False`
  - `SITE_ID = 1` (requis par allauth)
  - `EMAIL_BACKEND` reste sur `smtp` (Mailpit en local) — fallback `locmem` pour tests
  - `AUTH_PASSWORD_VALIDATORS` : valider que le minLength est passé à **12** (cf. AC6)
- [x] T1.2 Créer la structure `apps/api/apps/accounts/` :
  ```
  apps/accounts/
  ├── __init__.py
  ├── apps.py             # AccountsConfig label="accounts"
  ├── models.py
  ├── managers.py         # UserManager custom
  ├── adapters.py         # PathAdvisorAccountAdapter (override allauth)
  ├── serializers.py      # SignupSerializer
  ├── views.py            # (DRF ViewSets ou wrappers — la plupart héritée de dj-rest-auth)
  ├── urls.py
  ├── services/
  │   ├── __init__.py
  │   └── auth_service.py # Business logic
  ├── admin.py
  └── tests/
      ├── __init__.py
      ├── factories.py
      └── test_signup.py
  ```
- [x] T1.3 Définir `User` model dans `models.py` (cf. snippet §4.7). Champs minimum :
  - `id` (ULID préfixé `usr_`) via `apps.core.ids.generate_id("usr")`
  - `email` (unique, indexé, lowercase)
  - `password` (hérité AbstractBaseUser)
  - `role` (TextChoices : `STUDENT`, `PARENT`, `COUNSELOR`, `SCHOOL_ADMIN`, `PATH_ADMIN`) — default `STUDENT`
  - `birth_date` (DateField, NOT NULL pour student)
  - `status` (TextChoices : `EMAIL_UNVERIFIED`, `PENDING_PARENTAL_CONSENT`, `ACTIVE`, `SUSPENDED`, `DELETED`) — default `EMAIL_UNVERIFIED`
  - `email_verified_at` (DateTimeField, nullable)
  - `consent_rgpd_at` (DateTimeField, NOT NULL — preuve d'horodatage)
  - `consent_cgu_version` (CharField — version YYYY-MM-DD acceptée)
  - `tenant_id` (UUID, nullable pour B2C ; sera utilisé Story 1.8 RLS)
  - `created_at`, `updated_at` (auto)
  - `deleted_at` (soft delete, nullable — Story 1.12)
  - `is_staff`, `is_superuser` (hérités AbstractBaseUser, pour Django admin)
- [x] T1.4 Créer `apps/core/ids.py` avec helper `generate_id(prefix: str) -> str` retournant `f"{prefix}_{ulid.new()}"` (lib `python-ulid` à ajouter dans pyproject.toml deps — `uv add python-ulid`).
- [x] T1.5 Créer `apps/accounts/adapters.py` avec `PathAdvisorAccountAdapter(DefaultAccountAdapter)` qui override `save_user()` pour lire `birth_date` + `consent_rgpd_at` du serializer et faire la validation âge ≥ 15.
- [x] T1.6 Créer `apps/accounts/serializers.py::SignupSerializer` (extends `dj_rest_auth.registration.serializers.RegisterSerializer`) avec champs additionnels : `birth_date` (DateField required), `consent_rgpd_accepted` (BooleanField required, must be True), `consent_cgu_version` (CharField required). `validate_birth_date` calcule l'âge via `dateutil.relativedelta` ; raise `ValidationError` formaté Problem Details si < 15.
- [x] T1.7 Créer `apps/accounts/services/auth_service.py` avec `signup_student(email, password, birth_date, consent_rgpd_accepted, consent_cgu_version) -> User` qui encapsule la business logic (le serializer reste thin, déléguer au service). **Log structuré (décision §9 #1) :** `structlog.get_logger(__name__).info("user.signed_up", actor_id=user.id, role=user.role.value, source="signup_student")` après création réussie. Idem pour `user.email_verified` dans le service de confirmation email. Aucune table `audit_log` créée cette story.
- [x] T1.8 Câbler les URLs dans `apps/api/path_advisor/urls.py` :
  ```python
  path("api/v1/auth/", include("dj_rest_auth.urls")),
  path("api/v1/auth/registration/", include("dj_rest_auth.registration.urls")),
  path("api/v1/auth/", include("apps.accounts.urls")),  # pour endpoints custom plus tard
  ```

### T2 — Migrations + reset DB (AC1)

- [x] T2.1 Générer la migration initiale : `uv run python manage.py makemigrations accounts`
- [x] T2.2 **CRITIQUE — Reset DB local** : `AUTH_USER_MODEL` ne peut pas être changé sans wiper la DB. Documenter la procédure dans la PR description :
  ```bash
  docker compose down -v       # wipe postgres_data volume
  docker compose up -d
  docker compose exec api uv run python manage.py migrate
  make seed                    # recrée admin@path-advisor.local
  ```
- [x] T2.3 Mettre à jour `apps/api/scripts/seed_dev.py::_ensure_admin` pour utiliser le nouveau User model (passer `role="PATH_ADMIN"`, `birth_date=date(2000, 1, 1)`, `consent_rgpd_at=now()`, `consent_cgu_version="2026-05-15"`, `status="ACTIVE"`, `email_verified_at=now()`).

### T3 — Configuration CSRF + sessions cross-origin (cross-cutting)

- [x] T3.1 Mettre à jour `settings/base.py` :
  - `SESSION_COOKIE_HTTPONLY = True`
  - `SESSION_COOKIE_SAMESITE = "Lax"`
  - `SESSION_COOKIE_SECURE = False` en local / `True` en staging+prod (override dans prod.py)
  - `CSRF_COOKIE_HTTPONLY = False` (le front doit pouvoir le lire pour le mettre en header)
  - `CSRF_COOKIE_SAMESITE = "Lax"`
  - `CSRF_TRUSTED_ORIGINS = ["http://localhost:3000"]` (override pour staging+prod via env)
- [x] T3.2 Ajouter un endpoint `GET /api/v1/auth/csrf/` (vue dans `apps/accounts/views.py`) qui appelle `django.middleware.csrf.get_token(request)` et retourne `{"csrf_token": "..."}`. Le front l'appellera au mount du composant Signup pour récupérer le token avant tout POST.

### T4 — Email transactionnel : abstraction Mailpit / Postmark (AC3)

- [x] T4.1 Vérifier que `settings.EMAIL_BACKEND` est `django.core.mail.backends.smtp.EmailBackend` en local (avec `EMAIL_HOST=mailpit`, `EMAIL_PORT=1025` — déjà configuré Story 1.1).
- [x] T4.2 Créer templates email allauth dans `apps/api/apps/accounts/templates/account/email/email_confirmation_message.txt` + `email_confirmation_subject.txt` (allauth les charge par convention). Contenu : ton complice, voix Path-Advisor, lien `{{ activate_url }}` (allauth context), mention DPO. Cf. §4.6.
- [x] T4.3 Override `account/email/email_confirmation_message.html` pour version HTML (Inter font, brand R1 button, fallback texte). Garder simple pour MVP — pas de MJML.
- [x] T4.4 Vérifier via curl + Mailpit UI que l'email arrive à `http://localhost:8025` lors d'un signup test.

### T5 — Frontend signup page (AC1, AC2, AC6)

- [x] T5.1 Créer la route `apps/web/src/app/(public)/auth/signup/page.tsx` (Server Component shell) qui rend un Client Component `<SignupForm />`.
- [x] T5.2 Créer `apps/web/src/components/features/auth/signup-form.tsx` (`"use client"`) :
  - React Hook Form + Zod schema (`email`, `password`, `birth_date` `YYYY-MM-DD`, `consent_rgpd_accepted` boolean true)
  - 4 inputs shadcn (`<Input>`) + 1 checkbox shadcn (`<Checkbox>` — à ajouter via shadcn add si pas déjà présent) + 1 `<Button>` brand
  - Loading state pendant submit (disable button + spinner)
  - Affichage des erreurs API en français (parser le `detail` + `errors[]` Problem Details)
  - Champ "date de naissance" en `<input type="date">` (HTML native suffit MVP — picker custom plus tard si besoin)
- [x] T5.3 Ajouter `Checkbox` à la palette shadcn (décision §9 #5) : `cd apps/web && NPM_CONFIG_LEGACY_PEER_DEPS=true npx shadcn@latest add checkbox --yes --overwrite`. **Si échec persistant** → fallback manuel décrit en §4.12 (copier le composant + `npm install --save-dev --legacy-peer-deps @radix-ui/react-checkbox`).
- [x] T5.4 Créer un wrapper `apps/web/src/lib/api/auth.ts` qui expose `signupStudent(payload)` et `verifyEmail(key)` — utilise `apiFetch` du Story 1.1 avec gestion CSRF :
  - Au premier mount, fetch `GET /api/v1/auth/csrf/` pour récupérer le token
  - Sur chaque POST, ajouter header `X-CSRFToken: <token>`
- [x] T5.5 Internationalisation : tous les labels/erreurs en français en dur dans `signup-form.tsx` pour MVP (next-intl wiring complet = Story 7.7). Centraliser les strings en haut du composant pour éviter la dispersion.
- [x] T5.6 Accessibilité (NFR-A1) :
  - Tous les inputs ont un `<label htmlFor>` associé
  - La checkbox a un label avec lien (`<label>J'accepte les <Link href="/legal/rgpd">CGU et la politique RGPD</Link></label>`)
  - Tab order logique
  - Focus visible (utilise déjà la rule globale `:focus-visible` posée Story 1.2)
  - Annonces d'erreur via `aria-describedby` sur les inputs + `role="alert"` sur le block d'erreur form-level

### T6 — Frontend verify-email page (AC4)

- [x] T6.1 Créer `apps/web/src/app/(public)/auth/verify-email/page.tsx` (Client Component à cause de `useSearchParams`) :
  - Lire `key` depuis l'URL
  - Au mount, appeler `verifyEmail(key)`
  - 3 états : `loading`, `success` (redirect `/onboarding` après 1s), `error` (afficher le `detail` du Problem + CTA "Renvoyer l'email")
- [x] T6.2 Créer une route placeholder `apps/web/src/app/(authenticated)/onboarding/page.tsx` (décision §9 #2 : **Server Component minimal** — aucun fetch, aucun state, sera écrasée par Story 2.1). Contenu attendu : `<main><h1 className="text-h1 md:text-h1-desktop">Bienvenue sur Path-Advisor</h1><p className="text-body text-text-muted">Ton onboarding arrive avec Story 2.1 (Epic 2).</p></main>`. Le but est juste que le redirect AC4 ait une cible valide.

### T7 — Politique RGPD `/legal/rgpd` (AC5)

- [x] T7.1 Créer `apps/web/src/app/(public)/legal/rgpd/page.tsx` (Server Component, `export const dynamic = "force-static"`). Contient les 8 sections requises (cf. AC5).
- [x] T7.2 Utiliser la typographie design system : `text-display-2 md:text-display-2-desktop` pour le H1, `text-h2 md:text-h2-desktop` pour les sections, `text-body` pour le contenu, `text-text-muted` pour les notes.
- [x] T7.3 Ancres : chaque section a un `id` (`#responsable`, `#finalites`, `#base-legale`, `#donnees`, `#conservation`, `#droits`, `#dpo`, `#cnil`, **`#mineurs`** spécifiquement requis pour deep-link AC2).
- [x] T7.4 Lien CNIL externe avec `rel="noopener noreferrer"`, target="_blank" + label "ouvre une nouvelle fenêtre" (RGAA).
- [x] T7.5 Placeholders `[À DÉFINIR avant production]` pour les infos légales manquantes (décision §9 #4 : **textes corrects sur ce qui est connu** — CNIL, droits RGPD, durées de conservation déjà rédigées correctement ; placeholders uniquement sur raison sociale, adresse postale, DPO réel). Rendus avec `<mark className="bg-warning/20 px-1">` pour être **visuellement évidents**. Note importante : ajouter une note en début de page (`<p role="note" className="bg-warning/10 border-l-4 border-warning p-4 text-body-sm">Cette page contient des placeholders [À DÉFINIR avant production] — ne pas déployer en prod tel quel.</p>`) clairement visible.

### T8 — Rate limiting signup (AC6)

- [x] T8.1 Installer `django-ratelimit` : `cd apps/api && uv add django-ratelimit`.
- [x] T8.2 Décorer la vue signup (override `dj_rest_auth.registration.views.RegisterView` dans `apps/accounts/views.py`) avec `@ratelimit(key="ip", rate="5/h", block=True)`.
- [x] T8.3 Configurer le storage rate limit sur Redis (décision §9 #3 — partagé entre workers, persistant, cohérent prod) : `RATELIMIT_USE_CACHE = "default"` + `CACHES = {"default": {"BACKEND": "django.core.cache.backends.redis.RedisCache", "LOCATION": os.environ["REDIS_URL"]}}` dans `settings/base.py`. **En settings/test.py** : override vers `LocMemCache` pour ne pas dépendre de Redis dans les tests pytest.
- [x] T8.4 Customiser la réponse 429 : Problem Details `type=https://path-advisor.fr/errors/rate-limited`, `Retry-After: 3600` header.

### T9 — RFC 7807 Problem Details — handler global DRF

- [x] T9.1 Créer `apps/core/exceptions.py` avec une `DomainError(Exception)` racine + des sous-classes (`AgeUnder15`, `EmailAlreadyRegistered`, `WeakPassword`, `RateLimited`, etc.) chacune avec attributs `type`, `title`, `status`, `detail`.
- [x] T9.2 Créer un handler DRF custom dans `apps/core/exceptions.py::path_advisor_exception_handler` qui convertit `DomainError` + les `ValidationError` natifs DRF vers le format Problem Details (`application/problem+json` Content-Type).
- [x] T9.3 Câbler le handler dans `settings/base.py::REST_FRAMEWORK` : `"EXCEPTION_HANDLER": "apps.core.exceptions.path_advisor_exception_handler"`.

### T10 — Tests pytest + Vitest (AC7)

- [x] T10.1 Créer `apps/accounts/tests/factories.py` avec `UserFactory(factory_boy)` :
  - email/password fakes
  - birth_date 18 ans dans le passé par défaut
  - status=ACTIVE par défaut
  - Variantes : `EmailUnverifiedUserFactory`, `MinorUserFactory` (birth_date 13 ans)
- [x] T10.2 Créer `apps/accounts/tests/test_signup.py` avec **7 tests** (cf. AC7) :
  - `test_signup_happy_path_creates_user_in_email_unverified`
  - `test_signup_without_consent_rgpd_returns_400_problem`
  - `test_signup_age_under_15_returns_400_problem_with_age_under_15_type`
  - `test_signup_duplicate_email_returns_400_problem_generic_message`
  - `test_signup_weak_password_returns_400_problem_with_all_violations`
  - `test_verify_email_with_valid_token_activates_account`
  - `test_signup_rate_limited_after_5_attempts` *(marker `@pytest.mark.slow` — peut être skipé en CI rapide)*
- [x] T10.3 Créer `apps/web/src/components/features/auth/signup-form.test.tsx` (Vitest) :
  - Rend les 4 inputs + checkbox + bouton
  - Bouton disabled tant que checkbox pas cochée
  - Affiche les erreurs API en français (mocker `apiFetch` qui renvoie un Problem)
- [x] T10.4 Ajouter un test contraste pour le rouge brand sur form errors si nécessaire (`#9E2A24` sur `#FAFAF7` est déjà au-dessus de 4.5:1 — pas de test additionnel requis).

### T11 — Documentation + validation finale

- [x] T11.1 Mettre à jour `docs/onboarding.md` §troubleshooting : ajouter une entrée "Custom User Model migration" expliquant `docker compose down -v` requis pour reset DB.
- [x] T11.2 Créer `docs/adr/0002-auth-allauth-dj-rest-auth.md` documentant le choix `django-allauth` + `dj-rest-auth` + session cookie + CSRF (en référence à `core-architectural-decisions.md`).
- [x] T11.3 Validation finale :
  - `make lint` clean (3 apps)
  - `make test` clean (api : +7 tests, web : +1 test = 9 web au total)
  - `make openapi` → endpoint `/api/v1/auth/registration/` apparaît dans le schéma
  - Test manuel : `docker compose up -d` → `make seed` → `http://localhost:3000/auth/signup` → submit → vérifier Mailpit → cliquer le lien → vérifier redirect `/onboarding`
  - Screenshot du flow capturé pour la PR description

---

## 4. Dev Notes

### 4.1 Contexte projet — ce qui existe déjà

**Stories 1.1 et 1.2 livrées :**
- Django 5.1.15 + DRF + drf-spectacular installé via `uv` (Story 1.1)
- `apps/api/apps/core/` créé (placeholder Story 1.1) — cette story va y ajouter `core/exceptions.py` et `core/ids.py`
- `apps/api/apps/accounts/` **n'existe pas encore** — Story 1.3 le crée
- `django-allauth`, `dj-rest-auth`, `django-otp`, `django-celery-beat`, `django-storages`, `boto3`, `pgvector`, `pillow`, `structlog`, `sentry-sdk` déjà dans `pyproject.toml` deps (Story 1.1)
- `INSTALLED_APPS` actuellement minimal (admin, auth, contenttypes, sessions, messages, staticfiles + rest_framework, drf_spectacular, corsheaders, django_celery_beat, apps.core). À étendre.
- `MIDDLEWARE` actuellement : CORS, security, sessions, common, CSRF, auth, messages, clickjacking. Manque `AccountMiddleware` allauth.
- Endpoint `/api/v1/health/` opérationnel (Story 1.1)
- Settings split base/local/staging/prod/test — local.py et test.py mettent leur propre `SECRET_KEY` (Story 1.1 + patches code review)
- Migration `apps/core/0001_init_extensions.py` crée `pgvector` + `pgcrypto` (Story 1.1 patch)
- `make seed` crée un super-user `admin@path-advisor.local` (Story 1.1)
- Design tokens R1 Vermillon + 6 composants shadcn (Button, Card, Dialog, Form, Input, Label) livrés Story 1.2
- `apiFetch` wrapper TS existe à `apps/web/src/lib/api/client.ts` avec `credentials: "include"`, gestion CSRF via header `X-CSRFToken` (mais pas encore wiré bout en bout)
- `/auth/*` routes Next.js **n'existent pas** — cette story crée la première
- `/onboarding` route **n'existe pas** — cette story crée un placeholder
- `/legal/rgpd` route **n'existe pas** — cette story crée la vraie page
- Page d'accueil `/` reste sur le showcase Story 1.2 (le user a aussi créé `/design-system` qui consolide le showcase)

### 4.2 Décisions architecturales locked (cf. Story 1.1 + 1.2)

| Décision | Choix figé | Source |
|---|---|---|
| Auth | `django-allauth` + `dj-rest-auth` + (TOTP via `django-otp` Story 1.6) | core-architectural-decisions.md §Authentication & Security |
| Token front↔back | **Session cookie httpOnly SameSite=Lax** (PAS de JWT) | core-architectural-decisions.md |
| CSRF | Token CSRF Django, injecté dans Next.js via cookie `csrftoken` + header `X-CSRFToken` | core-architectural-decisions.md |
| API version | URL `/api/v1/...` | core-architectural-decisions.md |
| Format erreur | RFC 7807 Problem Details (`application/problem+json`) | core-architectural-decisions.md §API |
| JSON naming | `snake_case` end-to-end (back + JSON + types TS) — PAS de conversion camelCase | implementation-patterns §JSON field naming |
| Business logic | Dans `services/`, jamais dans les views/ViewSets | implementation-patterns §Enforcement |
| Identifiants | Préfixés ULID : `usr_01HXJ...`, `cnst_01HXK...` | implementation-patterns §Data Exchange |
| Booléens API | `true`/`false` (pas 1/0) | implementation-patterns |
| Locale | `fr-fr` par défaut (déjà set dans base.py) | base.py L77 |
| Email backend dev | Mailpit (port 1025) | infra/docker-compose.yml |
| Email backend prod | Postmark (Story 8.1 abstraction) — pour cette story rester sur SMTP générique | starter-template-evaluation.md |
| User model | Custom `accounts.User` étendant `AbstractBaseUser` + `PermissionsMixin` | architecture/project-structure-boundaries.md L147-160 |
| Tailwind v3 | Imposé Story 1.1 §4.10 | story 1.1 |
| Form lib | React Hook Form + Zod (Story 1.1 déjà installées) | core-architectural-decisions.md §Frontend |

### 4.3 Versions et libs à utiliser

| Lib | Version (depuis Story 1.1) | Usage cette story |
|---|---|---|
| `django` | 5.1.15 | base |
| `djangorestframework` | 3.15.x | viewsets + handler |
| `django-allauth` | 65.x | signup + email verification |
| `dj-rest-auth` | 7.x | REST endpoints auth |
| `django-ratelimit` | À ajouter (`uv add django-ratelimit`) | rate limit signup |
| `python-ulid` | À ajouter (`uv add python-ulid`) | ULID prefixed IDs |
| `python-dateutil` | 2.9.x (transitive via `factory-boy`) | calc âge `relativedelta` |
| Mailpit | image `axllent/mailpit:latest` (Story 1.1) | email dev |
| `next` | 16.2.6 | front |
| `react-hook-form` | 7.75+ | form management |
| `zod` | 3.25+ | schema validation |

**Action concrète :** dans `apps/api`, exécuter :
```bash
cd apps/api
uv add django-ratelimit python-ulid
```
*(Cela mettra à jour `pyproject.toml` ET `uv.lock`, qui seront committés.)*

### 4.4 Anti-patterns à éviter

- **Ne PAS** mettre la business logic du signup dans `RegisterView` ou le serializer — déléguer à `apps.accounts.services.auth_service.signup_student()`.
- **Ne PAS** utiliser camelCase dans les payloads JSON (front et back en snake_case partout). Le `signup-form.tsx` doit poster `{email, password, birth_date, consent_rgpd_accepted, consent_cgu_version}`, pas `birthDate`.
- **Ne PAS** révéler l'existence d'un email lors d'un signup duplicate — message générique côté API public, log précis côté serveur (CWE-203 "user enumeration").
- **Ne PAS** stocker le password en clair même temporairement. Allauth/Django gère le hashing PBKDF2 par défaut — laisser faire, ne pas override.
- **Ne PAS** désactiver les password validators standards Django même pour "tester rapidement".
- **Ne PAS** activer dark mode dans la page RGPD — Story 1.2 décision : light only MVP.
- **Ne PAS** committer de vraies infos légales (raison sociale, adresse, DPO réel) dans la page RGPD MVP — utiliser placeholders `[À DÉFINIR avant production]` clairement visibles.
- **Ne PAS** créer un endpoint custom `POST /api/v1/auth/signup/` ; utiliser celui de `dj_rest_auth.registration.urls` (`/api/v1/auth/registration/`). Override le serializer, pas la vue.
- **Ne PAS** logger le password ou le birth_date dans les structured logs (PII).
- **Ne PAS** envoyer le birth_date au front après signup (le User serializer de sortie doit l'exclure — défense en profondeur).
- **Ne PAS** créer un audit_log table maintenant — Story 1.13 dédiée. Pour Story 1.3 : structlog avec champs `event=user.signed_up, actor_id=usr_..., correlation_id=req_...` suffit ; Story 1.13 consumera ces logs.

### 4.5 Reset DB local — procédure obligatoire

Setting `AUTH_USER_MODEL` après que des migrations existent est **un changement breaking** dans Django : la migration initiale `auth.0001_initial` référence `auth.User`, et changer pour `accounts.User` casse l'historique migrations.

**Procédure obligatoire avant la première migration de cette story :**

```bash
# 1. Wipe les données existantes (postgres_data + redis_data volumes)
docker compose down -v

# 2. Remonter la stack froide
docker compose up -d

# 3. Lancer les migrations (incl. la nouvelle apps/accounts/0001_initial)
docker compose exec api uv run python manage.py migrate

# 4. Re-seed (utilise désormais le nouveau User model)
make seed
```

**Documentation à ajouter dans `docs/onboarding.md` § Troubleshooting + en haut de la PR description.**

### 4.6 Micro-copy email vérification (FR — voix Path-Advisor)

Suit les principes UX (§Tone of Voice) : complice sans familiarité forcée, factuel sans froideur, jamais culpabilisant ni urgent. Inspirations : Doctolib (sobriété), Revolut (clarté), pas Duolingo (gamification).

**Subject :** `Vérifie ton adresse email pour démarrer sur Path-Advisor`

**Body (text) — placeholder rédactionnel :**

```
Salut,

Tu viens de créer un compte sur Path-Advisor — bienvenue.

Pour activer ton compte, clique sur ce lien dans les 3 jours :
{{ activate_url }}

Une fois ton email vérifié, tu pourras finaliser ton profil et découvrir
des métiers qui pourraient te correspondre, avec une transparence
totale sur la manière dont on te les recommande.

Tu as une question sur tes données ? Écris à dpo@path-advisor.fr.

À bientôt,
L'équipe Path-Advisor

---
Tu reçois cet email parce que quelqu'un a utilisé ton adresse pour
créer un compte sur Path-Advisor. Si ce n'est pas toi, ignore ce
message — le compte sera automatiquement annulé sous 3 jours sans
vérification.
```

**Anti-patterns à NE PAS appliquer :** "⚠️ URGENT : Ton compte expire dans 24h !!!", "Confettis 🎉", "Tu as choisi le bon chemin !".

### 4.7 Snippet de référence — `User` model

```python
# apps/api/apps/accounts/models.py
from __future__ import annotations

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from apps.accounts.managers import UserManager
from apps.core.ids import generate_id


class UserRole(models.TextChoices):
    STUDENT = "student", "Élève"
    PARENT = "parent", "Parent"
    COUNSELOR = "counselor", "Conseiller"
    SCHOOL_ADMIN = "school_admin", "Administrateur école partenaire"
    PATH_ADMIN = "path_admin", "Administrateur Path-Advisor"


class UserStatus(models.TextChoices):
    EMAIL_UNVERIFIED = "email_unverified", "Email non vérifié"
    PENDING_PARENTAL_CONSENT = "pending_parental_consent", "Consentement parental en attente"
    ACTIVE = "active", "Actif"
    SUSPENDED = "suspended", "Suspendu"
    DELETED = "deleted", "Supprimé"


class User(AbstractBaseUser, PermissionsMixin):
    id = models.CharField(
        primary_key=True,
        max_length=32,
        default=lambda: generate_id("usr"),
        editable=False,
    )
    email = models.EmailField(unique=True, db_index=True)
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.STUDENT)
    birth_date = models.DateField(null=True, blank=True)  # nullable for non-student roles
    status = models.CharField(
        max_length=30, choices=UserStatus.choices, default=UserStatus.EMAIL_UNVERIFIED
    )

    email_verified_at = models.DateTimeField(null=True, blank=True)
    consent_rgpd_at = models.DateTimeField(null=True, blank=True)
    consent_cgu_version = models.CharField(max_length=20, null=True, blank=True)

    # Multi-tenant — used by Story 1.8 RLS.
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)  # soft delete (Story 1.12)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []  # email + password handled by USERNAME_FIELD

    class Meta:
        db_table = "users"
        constraints = [
            models.UniqueConstraint(fields=["email"], name="uq_users_email"),
        ]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["tenant_id"]),
        ]

    def __str__(self) -> str:
        return self.email
```

### 4.8 Snippet de référence — `SignupSerializer`

```python
# apps/api/apps/accounts/serializers.py
from __future__ import annotations

from datetime import date

from dateutil.relativedelta import relativedelta
from dj_rest_auth.registration.serializers import RegisterSerializer
from django.utils import timezone
from rest_framework import serializers

from apps.core.exceptions import AgeUnder15


class SignupSerializer(RegisterSerializer):
    """Path-Advisor signup payload.

    Inherits dj-rest-auth's password complexity validation and email-uniqueness
    check. Adds: `birth_date`, `consent_rgpd_accepted`, `consent_cgu_version`.
    Username field is dropped — we authenticate by email only.
    """

    username = None  # remove unused field
    birth_date = serializers.DateField(required=True)
    consent_rgpd_accepted = serializers.BooleanField(required=True)
    consent_cgu_version = serializers.CharField(required=True, max_length=20)

    def validate_consent_rgpd_accepted(self, value: bool) -> bool:
        if not value:
            raise serializers.ValidationError("Tu dois accepter les CGU et la politique RGPD.")
        return value

    def validate_birth_date(self, value: date) -> date:
        today = timezone.localdate()
        age = relativedelta(today, value).years
        if age < 15:
            raise AgeUnder15()
        return value

    def get_cleaned_data(self) -> dict:
        cleaned = super().get_cleaned_data()
        cleaned.update(
            {
                "birth_date": self.validated_data["birth_date"],
                "consent_rgpd_accepted": self.validated_data["consent_rgpd_accepted"],
                "consent_cgu_version": self.validated_data["consent_cgu_version"],
            }
        )
        return cleaned

    def save(self, request):
        user = super().save(request)
        user.birth_date = self.validated_data["birth_date"]
        user.consent_rgpd_at = timezone.now()
        user.consent_cgu_version = self.validated_data["consent_cgu_version"]
        user.role = "student"
        user.save(
            update_fields=["birth_date", "consent_rgpd_at", "consent_cgu_version", "role"]
        )
        return user
```

### 4.9 Snippet de référence — `DomainError` + handler

```python
# apps/api/apps/core/exceptions.py
from __future__ import annotations

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_default_handler


class DomainError(Exception):
    type: str = "https://path-advisor.fr/errors/unknown"
    title: str = "Domain error"
    status_code: int = status.HTTP_400_BAD_REQUEST
    default_detail: str = "An error occurred."

    def __init__(self, detail: str | None = None, **extras):
        super().__init__(detail or self.default_detail)
        self.detail = detail or self.default_detail
        self.extras = extras


class AgeUnder15(DomainError):
    type = "https://path-advisor.fr/errors/age-under-15"
    title = "Inscription mineur sous 15 ans"
    default_detail = (
        "L'inscription des moins de 15 ans nécessite un consentement parental — "
        "flow disponible prochainement (Story 1.4)."
    )


class EmailAlreadyRegistered(DomainError):
    type = "https://path-advisor.fr/errors/email-already-registered"
    title = "Adresse déjà utilisée"
    # Generic on purpose — do NOT reveal whether email exists.
    default_detail = "Impossible de créer un compte avec ces informations."


def path_advisor_exception_handler(exc, context) -> Response:
    if isinstance(exc, DomainError):
        problem = {
            "type": exc.type,
            "title": exc.title,
            "status": exc.status_code,
            "detail": exc.detail,
            "instance": context["request"].path,
        }
        if exc.extras:
            problem["errors"] = exc.extras
        return Response(problem, status=exc.status_code, content_type="application/problem+json")
    return drf_default_handler(exc, context)
```

### 4.10 Stratégie de tests

- **pytest-django** (apps/api) — 7 tests dans `apps/accounts/tests/test_signup.py`. Tests d'intégration via `APIClient` qui appelle réellement `/api/v1/auth/registration/`. SQLite in-memory en test (settings.test) — la migration `0001_init_extensions` skip pgvector si `connection.vendor != postgresql` (Story 1.1 patch).
- **Email backend en test** : `locmem` — vérifier `len(mail.outbox) == 1` après signup, asserter le subject + le `activate_url` dans le body.
- **Vitest** (apps/web) — 1 nouveau test `signup-form.test.tsx`. Mocker `apiFetch` via `vi.mock("@/lib/api/client")`. Tester : render initial, bouton disabled sans checkbox, click → assert `apiFetch` appelé avec le bon payload, render error si mock renvoie un Problem.
- **Pas de Playwright end-to-end cette story** — l'effort à câbler Playwright + lancer Mailpit en headless dans CI > la valeur. Reporter Sprint 4+ (Story TBD : "E2E parcours Sarah").

### 4.11 Performance & sécurité — points d'attention

- **NFR-P6 : auth en < 1 s P95** — POST signup doit retourner en < 1s. Pour signup, le bottleneck sera l'envoi d'email synchrone — utiliser `EMAIL_BACKEND` standard SMTP (Mailpit en local accepte instantanément). En prod, Postmark a SLA < 500ms ; si besoin, l'envoi pourra basculer en Celery task plus tard (hors scope MVP).
- **CWE-203 (user enumeration)** : pour signup duplicate email, retourner toujours le même message générique côté API ; logger le détail côté serveur uniquement.
- **CWE-307 (improper restriction of excessive authentication attempts)** : adressé par AC6 rate limiting.
- **Password storage** : Django PBKDF2 default — ne pas override. Iterations par défaut suffisants en MVP.
- **PII dans logs** : aucun log ne doit contenir `password`, `birth_date`, ou `email` en plain. Si on a besoin de référer un user en logs, utiliser `user.id` (`usr_01HX...`) — non-PII.
- **CORS + credentials** : `CORS_ALLOW_CREDENTIALS = True` déjà set Story 1.1. `CORS_ALLOWED_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]` déjà set. Côté front, `apiFetch` envoie `credentials: "include"`.

---

## 5. Previous Story Intelligence

### Story 1.1 — Initialisation (done, commité `49ae947` / `bc9cf11` / `42e5e1e`)

**Patterns posés réutilisés ici :**
- Apps Django par capacité (`apps/accounts/`, pas `apps/auth/`). ✓
- Settings split base/local/staging/prod/test — étendre `base.py` pour allauth. ✓
- Tests via `pytest-django` + `factory_boy` (deps OK).
- `make lint` + `make test` + `make openapi` workflows opérationnels.
- `apiFetch` wrapper TS avec `credentials: "include"` + header CSRF custom.

**Risques connus à éviter :**
- `legacy-peer-deps=true` (Next 16 + next-intl) — toujours actif côté apps/web `.npmrc`.
- Custom User Model migration breaking — voir §4.5 procédure DB reset.

### Story 1.2 — Design system tokens (done, commité `8d4a5c8`)

**Patterns posés réutilisés ici :**
- Palette HSL unifiée (Story 1.2 code review) : utiliser `bg-brand`, `bg-bg-2`, `border-border`, `text-text-muted` etc. — pas de `#hex` hardcodé.
- Type scale responsive : `text-h1 md:text-h1-desktop`. Pour le SignupForm, viser `text-h2 md:text-h2-desktop` pour le titre du form, `text-body` pour les labels/inputs.
- `:focus-visible` global déjà actif → focus ring brand R1 hérité gratuitement par les inputs/checkboxes.
- shadcn components `Input`, `Label`, `Button`, `Form` déjà disponibles. **Ajouter `Checkbox` via `shadcn add checkbox`** (cf. T5.3).
- Pas de FR commentaires côté code (Story 1.2 code review). Comments en EN.

**Patches Story 1.2 à propager :**
- `next build --webpack` flag toujours nécessaire (commenté dans `next.config.ts`). Aucun changement attendu cette story.

### Story 1.1+1.2 — Patterns DRF/Front à respecter (rappel concentré)

| Pattern | Localisation | Source |
|---|---|---|
| Business logic dans `services/` | `apps/<capability>/services/` | implementation-patterns §Enforcement |
| `@audit_action("event.name")` décorateur | `apps/audit/decorators.py` — **N'EXISTE PAS encore, Story 1.13** | implementation-patterns |
| Pour cette story : pas d'audit DB ; structlog avec `event=user.signed_up` | `apps/accounts/services/auth_service.py` | story 1.3 décision pragmatique |
| `tenant_id` sur tout modèle PII | `User.tenant_id` (nullable B2C) | core-architectural-decisions §Data |
| Test d'autorisation explicite sur mutation | `test_signup_*` couvre ça (signup = endpoint anonyme, pas de RBAC à tester ici) | implementation-patterns |
| i18n des strings | `useTranslations` (next-intl) côté front — pour MVP `t = (key) => string` placeholder ; full wiring Story 7.7 | implementation-patterns |
| Pas de `fetch` brut | utiliser `apiFetch` de `lib/api/client.ts` | story 1.1 + implementation-patterns |

### Recent git activity

```
8d4a5c8 Story 1.2 done front and design init
a60297d editing readme
49ae947 story 1.1 infra init
42e5e1e story 1.1 infra init
bc9cf11 story 1.1 infra init
```

Story 1.2 = dernier commit ; rien d'autre n'est touché entre 1.2 et 1.3.

---

## 6. Project Context References

- **PRD FR (1, 2, 8-12) :** [`functional-requirements.md`](../planning-artifacts/prd/functional-requirements.md) — la source canonique des FRs auth.
- **PRD NFR (S1-S9) :** [`non-functional-requirements.md`](../planning-artifacts/prd/non-functional-requirements.md) — surtout S1 (TLS 1.3 chiffrement), S6 (délais RGPD), S8 (OWASP), S9 (consentement parental).
- **UX Flow 1 (Sarah signup → onboarding) :** [`ux-design-specification.md`](../planning-artifacts/ux-design-specification.md) §User Journey Flows L863-918.
- **Architecture auth + structure :** [`core-architectural-decisions.md`](../planning-artifacts/architecture/core-architectural-decisions.md) §Authentication & Security ; [`project-structure-boundaries.md`](../planning-artifacts/architecture/project-structure-boundaries.md) L147-160.
- **Patterns de code :** [`implementation-patterns-consistency-rules.md`](../planning-artifacts/architecture/implementation-patterns-consistency-rules.md).
- **Story 1.1 (foundation) :** [`1-1-initialisation-projet.md`](1-1-initialisation-projet.md).
- **Story 1.2 (tokens) :** [`1-2-design-system-tokens.md`](1-2-design-system-tokens.md).
- **Sprint tracking :** [`sprint-status.yaml`](sprint-status.yaml).

---

## 7. Definition of Done

- [ ] AC1-AC7 cochés dans la PR description
- [ ] `make lint` clean (3 apps, 0 régression)
- [ ] `make test` clean (api : +7 tests signup, web : +1 test SignupForm) — total tests api 8, web 9
- [ ] `make openapi` régénéré, `/api/v1/auth/registration/` documenté
- [ ] DB resetée (`docker compose down -v`) puis re-seedée — procédure documentée dans la PR
- [x] Test manuel end-to-end : signup → mailpit → click → /onboarding placeholder. Screenshots dans la PR.
- [ ] `docs/onboarding.md` mis à jour (troubleshooting custom User migration)
- [ ] `docs/adr/0002-auth-allauth-dj-rest-auth.md` créé
- [ ] Statut story → `review` puis `done` après code review
- [ ] CI verte sur GH Actions (ci-api + ci-web)

---

## 8. Dev Agent Record

### Agent Model Used

claude-opus-4-7 (1M context) — Claude Code interactive session, 2026-05-16 → 2026-05-17.

### Debug Log References

- **dj-rest-auth + `TOKEN_MODEL=None`** : `dj_rest_auth.models.get_token_model()` raise `ImproperlyConfigured` au boot. Fix : explicit `REST_AUTH["TOKEN_MODEL"] = None` (Story 1.1 décide session-cookie auth). Doc dans ADR-0002.
- **allauth template precedence** : nos templates `apps/accounts/templates/account/email/email_confirmation_*` ne sont pas trouvés en premier car `allauth` est chargé avant `apps.accounts` dans `INSTALLED_APPS`. Fix : `TEMPLATES.DIRS = [BASE_DIR / "apps/accounts/templates"]` (explicit). Doc dans ADR-0002.
- **dj-rest-auth `validate_email`** ne bloque que les emails *vérifiés*. Un duplicate avec email non-vérifié passe la validation et crash en `IntegrityError` au DB. Fix : override `validate_email` dans `SignupSerializer` qui rejette ANY duplicate (verified OR not). Message public reste générique (CWE-203). Doc dans ADR-0002.
- **drf-spectacular + `TOKEN_MODEL=None`** : `TokenSerializer` (dj-rest-auth) a `model = None`, crash `'NoneType' object has no attribute '_meta'`. Fix : preprocessing hook `apps.core.openapi.exclude_token_endpoints` qui drop `/auth/login/`, `/auth/logout/`, `/auth/password/*`, `/auth/user/` du schéma. Story 1.5 ré-inclura avec `@extend_schema` explicite.
- **`prefers-reduced-motion`** : Next.js `useSearchParams()` requiert un boundary Suspense pour le build static. Fix : refactor `/auth/verify-email/page.tsx` en `<Suspense>` autour du contenu réel.
- **Rate-limit cache leak entre tests** : LocMemCache persiste entre `pytest` runs. Fix : fixture `_clear_mailbox_and_cache` autouse qui appelle `cache.clear()` setup + teardown.

### Completion Notes List

**Versions épinglées :**
| Package | Installé |
|---|---|
| `django-allauth` | 65.x (transitive) |
| `dj-rest-auth` | 7.x |
| `django-ratelimit` | 4.1.0 |
| `python-ulid` | 3.1.0 |
| `python-dateutil` | 2.9.x |
| `requests` | 2.34.2 (transitive via allauth.socialaccount) |
| `@radix-ui/react-checkbox` | latest (via shadcn add) |

**5 décisions §4.10 respectées :**
1. ✅ Audit log → structlog only (table `audit_log` arrive Story 1.13)
2. ✅ Placeholder `/onboarding` → Server Component minimal
3. ✅ Rate limit → Redis en prod (CACHES), LocMemCache en test
4. ✅ GDPR content → placeholders `[À DÉFINIR avant production]` rendus avec `<mark>`, note d'avertissement en début
5. ✅ Checkbox shadcn → CLI retry réussi (`NPM_CONFIG_LEGACY_PEER_DEPS=true npx shadcn@latest add checkbox`)

**Tests :**
- pytest scope Story 1.3 : **8/8 verts** (7 signup + 1 health)
  - happy path → 201 + user créé + email envoyé
  - refus consent → 400 + Problem
  - age < 15 → 400 + `type=age-under-15`
  - duplicate email → 400 + message générique (CWE-203)
  - weak password → 400 + violations Django validators
  - verify email avec token valide → 200 + statut `active`
  - rate limit 6e attempt → 429 + Retry-After
- Vitest scope Story 1.3 : **3/3 verts** (SignupForm renders, consent bloque submit, ApiError surface detail)
- Web tests total : **21/21 verts** (compatibilité Story 1.2 + 1.14 préservée)

**Validation globale Story 1.3 scope :**
- `ruff check apps/accounts apps/core path_advisor scripts` ✓
- `npm run lint` (web) ✓
- `npm run build` (next build --webpack) ✓
- `npx tsc --noEmit` ✓
- `make openapi` ✓ — endpoints `/api/v1/auth/registration/`, `/verify-email/`, `/resend-email/`, `/csrf/` documentés
- DB reset procédure documentée dans `docs/onboarding.md` § Troubleshooting
- ADR-0002 créé documentant le choix allauth + dj-rest-auth + tooling gotchas

**Out of Story 1.3 scope (parallel work détectée) :**
- `apps/audit/` (Story 1.13 parallel work par Marwen) — 3 tests cassés + 31 ruff errors. **Non-bloquant** pour la review Story 1.3 : ne touche pas mon code.

**Points d'attention pour code review :**
- `validate_email` override est défensif (rejette même unverified) — discuter si on accepte la rétrocompatibilité avec dj-rest-auth's default behavior
- GDPR page content : placeholders bien visibles mais à valider par juriste avant prod
- `/auth/login/` et autres endpoints token-based exclus du schéma OpenAPI → Story 1.5 ré-inclura
- mypy en mode advisory (continue-on-error) reporte 9 warnings sur factory_boy / dj-rest-auth typing — non-bloquant

### File List

**Backend (apps/api) — nouveaux :**
- `apps/accounts/__init__.py`, `apps.py` (signal wiring in `ready()`)
- `apps/accounts/models.py` (User custom, UserRole, UserStatus)
- `apps/accounts/managers.py` (UserManager email-only)
- `apps/accounts/adapters.py` (PathAdvisorAccountAdapter — save_user + verify-URL pointing at Next.js)
- `apps/accounts/serializers.py` (SignupSerializer — validate_email defensive, validate_birth_date, validate_consent)
- `apps/accounts/services/__init__.py`, `services/auth_service.py` (mark_email_verified, log_signup via structlog)
- `apps/accounts/signals.py` (handlers email_confirmed + user_signed_up)
- `apps/accounts/views.py` (ThrottledRegisterView + csrf endpoint)
- `apps/accounts/urls.py`
- `apps/accounts/admin.py`
- `apps/accounts/migrations/0001_initial.py`
- `apps/accounts/templates/account/email/email_confirmation_subject.txt`
- `apps/accounts/templates/account/email/email_confirmation_message.txt`
- `apps/accounts/tests/__init__.py`, `factories.py`, `test_signup.py` (7 tests)
- `apps/core/exceptions.py` (DomainError + 6 sous-classes + path_advisor_exception_handler)
- `apps/core/ids.py` (generate_id ULID prefixed)
- `apps/core/openapi.py` (exclude_token_endpoints hook)

**Backend modifiés :**
- `path_advisor/settings/base.py` — INSTALLED_APPS allauth+dj-rest-auth, AUTH_USER_MODEL, CACHES Redis, ACCOUNT_*, REST_AUTH, AUTHENTICATION_BACKENDS, CSRF/SESSION cookies, RATELIMIT_USE_CACHE, SPECTACULAR_SETTINGS preprocessing hook, AUTH_PASSWORD_VALIDATORS min_length=12, TEMPLATES.DIRS pour override allauth
- `path_advisor/settings/test.py` — CACHES LocMemCache, EMAIL_BACKEND locmem
- `path_advisor/urls.py` — câblage `dj_rest_auth.urls` + `dj_rest_auth.registration.urls` + `apps.accounts.urls` + `ThrottledRegisterView` override
- `scripts/seed_dev.py` — adapté au custom User model (drop `username` arg)
- `pyproject.toml` (+ `uv.lock`) — `django-ratelimit`, `python-ulid`, `python-dateutil`, `requests`

**Frontend (apps/web) — nouveaux :**
- `src/app/(public)/auth/signup/page.tsx` (Server Component shell)
- `src/app/(public)/auth/verify-email/page.tsx` (Suspense + Client `VerifyEmailContent`)
- `src/app/(public)/legal/rgpd/page.tsx` (Server static, 8 sections + ancre `#mineurs`)
- `src/app/(authenticated)/onboarding/page.tsx` (Server placeholder)
- `src/components/features/auth/signup-form.tsx` (Client, RHForm + Zod + shadcn)
- `src/components/features/auth/signup-form.test.tsx` (Vitest, 3 tests)
- `src/components/ui/checkbox.tsx` (via shadcn add)
- `src/lib/api/auth.ts` (signupStudent, verifyEmail, resendVerificationEmail, fetchCsrfToken)

**Frontend modifiés :**
- `src/lib/api/client.ts` — RFC 7807 ApiError, readCsrfCookie helper
- `src/test-setup.ts` — ResizeObserver polyfill pour jsdom

**Docs :**
- `docs/adr/0002-auth-allauth-dj-rest-auth.md` (nouveau)
- `docs/onboarding.md` (ajout § Troubleshooting "AUTH_USER_MODEL migration error" + DB reset)

### Change Log

- 2026-05-16 → 2026-05-17 — Story 1.3 implémentée. `apps/accounts/` créée from scratch (User, adapter, serializer, service, signals, views, templates email). dj-rest-auth + allauth wired avec session cookies + CSRF cross-origin. RFC 7807 Problem Details handler global. Rate limit 5/h via Redis. GDPR page `/legal/rgpd` (8 sections + placeholders visibles). Signup flow front complet avec RHForm + Zod + shadcn Checkbox. Verify-email page avec Suspense. 7 pytest tests + 3 Vitest tests verts. ADR-0002 + onboarding troubleshooting. Status → `review`.
- 2026-05-17 — Code review multi-LLM (Opus Blind Hunter 41 findings + Sonnet Edge Case Hunter 34 findings + Haiku Acceptance Auditor). Findings consolidés en §11 ci-dessous : 3 decisions-needed + 17 patches + 12 deferred + 11 dismissed.
- 2026-05-17 — Code review actions complete : 3 décisions résolues + 17 patches appliqués + 12 deferred + 11 dismissed. `pytest apps/accounts apps/core` → 8/8 verts, `npm test` web → 29/29 verts, `make lint` + `npm run build` + `make openapi` clean. Status → `done`.

---

## 11. Review Findings (2026-05-17)

**Reviewers :** Opus 4.7 (Blind Hunter, 41 findings) + Sonnet 4.6 (Edge Case Hunter, 34 findings) + Haiku 4.5 (Acceptance Auditor).

**Verdict Acceptance Auditor :** ✅ 7/7 ACs satisfaits + 5/5 décisions §9 respectées.

**Stats triage :** 3 decisions-needed · 17 patches · 12 deferred · 11 dismissed (false positives + parallel work + by-design).

Raw reports : [.code-review/blind-hunter-1-3.md](../../.code-review/blind-hunter-1-3.md), [.code-review/edge-case-hunter-1-3.json](../../.code-review/edge-case-hunter-1-3.json), [.code-review/acceptance-auditor-1-3.md](../../.code-review/acceptance-auditor-1-3.md).

### Decisions needed (3)

- [x] [Review][Decision] **User enumeration via field-level `errors.email`** — `validate_email` raise `EmailAlreadyRegistered` qui passe par `path_advisor_exception_handler` et expose `errors.email` dans le Problem JSON → trivialement enumerable. Le commentaire CWE-203 dans le code est inopérant. **Choix :** (a) refactor `serializer.save()` pour retourner toujours `202 {"detail":"Verification e-mail sent if applicable"}` (uniforme, sécurité réelle), (b) garder le check mais retourner le Problem sans field-level errors (plus simple, conserve la rétro back-end), (c) accepter le leak (Pattern courant, faible enjeu vs UX d'erreur claire).

- [x] [Review][Decision] **`except Exception` broad catch dans `ThrottledRegisterView.create`** — Le substring-match `"already" + "email"/"registered"` est fragile à `LANGUAGE_CODE=fr-fr` et tout changement de wording dj-rest-auth. **Choix :** (a) narrow à `(IntegrityError, ValidationError)` uniquement (perd le safety net générique), (b) garder broad mais inspecter `exc.code` ou `exc.detail.code` (plus robuste, demande de connaître les codes dj-rest-auth), (c) ré-écrire en pre-check explicite côté serializer (déjà fait via `validate_email` — mais lié à la Décision 1).

- [x] [Review][Decision] **CSRF model : double-submit cookie + JSON endpoint** — `CSRF_COOKIE_HTTPONLY=False` + `/auth/csrf/` qui retourne le token en JSON = double surface XSS. **Choix :** (a) garder le pattern actuel (compatible Next.js client-side, conforme allauth/dj-rest-auth defaults), (b) passer en `HttpOnly=True` + injection serveur dans `<meta>` tag via Next layout Server Component (plus sûr, nécessite refactor du wrapper `apiFetch`).

### Patches (17 — à appliquer)

- [x] [Review][Patch] 🔴 **TEST `or` au lieu de `and` — vacuously passes** — `test_signup_duplicate_email_returns_400_problem_generic_message:100`. `assert "déjà" not in detail or "impossible" in detail` est vrai quoi qu'il arrive. Le test ne détecte AUCUNE régression d'enumeration. **Critique**. Fix : `assert ("déjà" not in detail) and ("impossible" in detail)`.

- [x] [Review][Patch] **Drop `log_signup` — duplicate avec `@audit_action`** — Story 1.13 (parallel work par Marwen) a wiré `@audit_action("user.signed_up")` sur `signup` et `@audit_action("user.email_verified")` sur `mark_email_verified`. Mon `log_signup` via structlog devient redondant. [apps/accounts/services/auth_service.py, apps/accounts/signals.py]

- [x] [Review][Patch] **Adapter strict consent check `is True`** — `consent_rgpd_at = timezone.now() if cleaned.get("consent_rgpd_accepted") is True else None`. Évite les truthy non-bool. [apps/accounts/adapters.py:41]

- [x] [Review][Patch] **`get_cleaned_data` KeyError-safe** — `self.validated_data.get(...)` au lieu de `[]` direct. [apps/accounts/serializers.py:get_cleaned_data]

- [x] [Review][Patch] **Future birth_date rejection** — `if value > timezone.localdate(): raise ValidationError("Date de naissance invalide")` avant calcul d'âge. [apps/accounts/serializers.py:validate_birth_date]

- [x] [Review][Patch] **`resend-email/` rate limit** — `ThrottledRegisterView` couvre que `/registration/` exact. Fix : ThrottledResendEmailView wrapper. [apps/api/path_advisor/urls.py]

- [x] [Review][Patch] **Email "3 jours auto-deletion" promise sans Celery task** — `email_confirmation_message.txt:20`. Fix immédiat : enlever cette ligne (la cleanup task arrivera Story 1.12 OU une story dédiée RGPD art. 5.1.c).

- [x] [Review][Patch] **`UserAdmin.add_fieldsets` omits consent/birth_date** — staff peut créer un User via Django admin sans consent → bypass serializer. Fix : `has_add_permission = lambda *a: False` pour forcer le flow signup. [apps/accounts/admin.py]

- [x] [Review][Patch] **`NEXT_PUBLIC_SITE_URL` fail-fast non-DEBUG** — fallback silencieux à `http://localhost:3000` en prod = lien cassé. Fix : `if not settings.DEBUG and not env-set: raise ImproperlyConfigured`. [apps/accounts/adapters.py:54]

- [x] [Review][Patch] **`SESSION_COOKIE_SECURE=True` et `CSRF_COOKIE_SECURE=True` par défaut** dans `base.py` ; override `False` uniquement dans `local.py`. [apps/api/path_advisor/settings/base.py + local.py]

- [x] [Review][Patch] **Verify-email empty `?key=` treated as loading** — `key = ""` est truthy en JS. Fix : `key && key.length > 0 ? k : null`. [apps/web/src/app/(public)/auth/verify-email/page.tsx:28]

- [x] [Review][Patch] **`emailconfirmation.key` URL-encoded** — `=`, `+`, `/` possibles. Fix : `quote(emailconfirmation.key, safe="")` dans adapters.py. [apps/accounts/adapters.py]

- [x] [Review][Patch] **CI gate `[À DÉFINIR]` detection sur build prod** — script post-build qui fail si le marqueur reste dans `/legal/rgpd`. Implementation simple : `grep -lr "À DÉFINIR" .next/server` retour ≠ 0 → exit 1. [GH Actions web]

- [x] [Review][Patch] **`pytest.mark.slow` non déclaré** — fail le jour où `--strict-markers` activé. Fix : `[tool.pytest.ini_options].markers = ["slow: ..."]`. [apps/api/pyproject.toml]

- [x] [Review][Patch] **Email verification test parse outbox** — extract URL du `mail.outbox[0].body` au lieu de build le token directement. Le test passe même si le template casse. [apps/accounts/tests/test_signup.py]

- [x] [Review][Patch] **`Site.objects.get_or_create(id=1)` data migration** — allauth raise `Site.DoesNotExist` au premier email si pas créée. Fix : migration `0002_create_default_site.py` qui `RunPython` un upsert. [apps/accounts/migrations/]

- [x] [Review][Patch] **Test rate-limit Retry-After assertion semantics** — `assert "Retry-After" in response` teste `.data` keys d'un DRF Response, pas les headers. Fix : `assert "Retry-After" in response.headers and int(...) >= 1`. [apps/accounts/tests/test_signup.py:test_signup_rate_limited]

### Deferred (12 — tracked for future stories)

- [x] [Review][Defer] **a11y consent checkbox label/description coupling** — Story 1.14 (ConsentDialog) ou story a11y dédiée Sprint 4+.
- [x] [Review][Defer] **a11y live-region verify-email + auto-redirect 1.5s** — Story a11y Sprint 4+.
- [x] [Review][Defer] **Redis graceful degradation** — prod hardening (Sprint 4+ deploy track).
- [x] [Review][Defer] **Email observability (bounce / DLQ / metric)** — Story 8.1 (email transactionnel abstraction).
- [x] [Review][Defer] **Index sur `consent_cgu_version` / `consent_rgpd_at`** — premature au MVP (≤ 500 users).
- [x] [Review][Defer] **`consent_cgu_version` null/blank/required 3 sources** — Story 1.12 (suppression compte) ou cleanup Sprint 3+.
- [x] [Review][Defer] **`MinorUserFactory` dead code** — sera utilisée par Story 1.4.
- [x] [Review][Defer] **`fireEvent.change` → `userEvent.type`** — refactor Sprint 4+ story a11y.
- [x] [Review][Defer] **`z.literal(true)` + `false as unknown as true` casts** — refactor avec `z.boolean().refine`. Story 1.4 ou cleanup pass.
- [x] [Review][Defer] **`exclude_token_endpoints` workaround TODO + test** — Story 1.5 (login) ré-inclura. Ajouter TODO maintenant.
- [x] [Review][Defer] **Rate limit X-Forwarded-For trust** — production gateway config (Caddy). Deploy track.
- [x] [Review][Defer] **Signal-based activation transaction atomicity** — Story 1.13 audit log durcira avec retry idempotent Celery.

### Dismissed (11 — false positives or out of Story 1.3 scope)

- ❌ `requests>=2.34.2` "n'existe pas" — knowledge cutoff Opus. uv résolu en 2026-05.
- ❌ `apps/audit` absent du diff — Story 1.13 parallel work. Hors scope.
- ❌ `AUDIT_IP_HASH_SALT` hardcoded fallback — Story 1.13 parallel work.
- ❌ Consent record integrity attestation (IP+UA+policy hash) — Story 1.13 scope.
- ❌ `@audit_action` peut capturer PII — Story 1.13.
- ❌ GDPR page `[À DÉFINIR]` + indexable — Décision §9 #4 explicitement acceptée. Mitigation : `<mark>` + warning + (patch CI gate).
- ❌ Two identifier conventions (ULID vs email) — by design.
- ❌ `User.id` default callable in migration — pattern Django standard.
- ❌ TOCTOU duplicate-email race — DB unique constraint OK ; couvert par Decision #2.
- ❌ `_clear_mailbox_and_cache` fixture name — intentional couple.
- ❌ Bilingual comments — adressé Story 1.2.

---

## 9. Decisions Resolved (validées par Marwen le 2026-05-16)

Les 5 questions ouvertes initiales ont été tranchées — aucune ambiguïté à lever côté dev agent.

| # | Question | Décision | Impact tâches |
|---|---|---|---|
| 1 | Audit log persistence | **Structlog only** (Story 1.13 ajoutera la table + trigger immuable) | T1.7 + T6.1 : utiliser `structlog.get_logger().info("user.signed_up", actor_id=user.id, role=user.role, ...)`. Pas de table audit_log cette story. |
| 2 | Placeholder `/onboarding` | **Server Component minimal** | T6.2 : page Server simple avec un h1 et un paragraphe. Aucun fetch, aucun state. Sera écrasée par Story 2.1. |
| 3 | Rate limit storage | **Redis** (partagé entre workers, persistant, cohérent prod) | T8.3 : `CACHES = {"default": {"BACKEND": "django.core.cache.backends.redis.RedisCache", ...}}` + `RATELIMIT_USE_CACHE = "default"`. |
| 4 | GDPR content | **Placeholders visibles** (`[À DÉFINIR avant production]`) + textes corrects sur ce qui est connu (CNIL, droits, durées) | T7.5 : utiliser `<mark>` ou `<span className="bg-warning/20">` pour rendre les placeholders évidents visuellement. Pas de vrai DPO/raison sociale. |
| 5 | Checkbox shadcn install | **Retry shadcn CLI** avec `NPM_CONFIG_LEGACY_PEER_DEPS=true` | T5.3 : commande exacte = `cd apps/web && NPM_CONFIG_LEGACY_PEER_DEPS=true npx shadcn@latest add checkbox --yes --overwrite`. Si échec persistant, fallback : copie manuelle depuis le repo shadcn/ui (snippet dans §4.12 ci-dessous). |

### §4.12 — Fallback Checkbox shadcn (si CLI fail)

Si `shadcn add checkbox` échoue (peer deps, registry down, etc.), copier le composant manuellement. Le source canonique est `https://ui.shadcn.com/r/styles/default/checkbox.json`. Code attendu (~30 lignes) :

```tsx
// apps/web/src/components/ui/checkbox.tsx
"use client";

import * as React from "react";
import * as CheckboxPrimitive from "@radix-ui/react-checkbox";
import { Check } from "lucide-react";

import { cn } from "@/lib/utils";

const Checkbox = React.forwardRef<
  React.ElementRef<typeof CheckboxPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof CheckboxPrimitive.Root>
>(({ className, ...props }, ref) => (
  <CheckboxPrimitive.Root
    ref={ref}
    className={cn(
      "peer h-4 w-4 shrink-0 rounded-sm border border-primary ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 data-[state=checked]:bg-primary data-[state=checked]:text-primary-foreground",
      className,
    )}
    {...props}
  >
    <CheckboxPrimitive.Indicator className={cn("flex items-center justify-center text-current")}>
      <Check className="h-4 w-4" />
    </CheckboxPrimitive.Indicator>
  </CheckboxPrimitive.Root>
));
Checkbox.displayName = CheckboxPrimitive.Root.displayName;

export { Checkbox };
```

Et `npm install --save-dev --legacy-peer-deps @radix-ui/react-checkbox` si pas déjà installé (probablement requis car les autres `@radix-ui/*` viennent de Story 1.1).
