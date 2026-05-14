# Epic 7 : Découverte Publique & SEO

Permettre l'acquisition organique : Sarah trouve Path-Advisor via Google sur une recherche "que faire après le bac" ou "devenir ingénieure biomédicale" et arrive sur une page métier indexable, performante, conforme Core Web Vitals.

## Story 7.1 : Pages publiques SSR — fiches métier indexables

As a moteur de recherche (Google, Bing) et acquisition organique,
I want une URL canonique stable et indexable par métier (`/metiers/{slug}`),
So that les pages métiers Path-Advisor apparaissent sur les recherches "devenir X" (FR46 + ADD-6).

**Acceptance Criteria :**

**Given** une fiche métier seed (Story 3.2)
**When** je visite `/metiers/ingenieure-biomedicale` sans être connecté
**Then** la page est rendue en SSR (Next.js) avec contenu HTML complet visible avant JavaScript
**And** je vois description + journée type + revenu médian + prérequis + parcours types (variants publics anonymes des graphes)
**And** un CTA "Crée ton compte pour voir tes chances réelles" invite à l'inscription

**Given** la performance (NFR-P3)
**When** Google PageSpeed Insights audite la page
**Then** TTFB < 1 s, LCP mobile < 2,5 s, FID < 100 ms, CLS < 0,1 (Core Web Vitals au vert)
**And** le HTML est cachable côté CDN (TTL 1h, revalidation On-Demand sur signalement)

**Given** la conformité accessibilité publique
**When** un utilisateur sans compte consulte la page
**Then** elle est RGAA AA (NFR-A1)
**And** elle est lisible avec JavaScript désactivé

## Story 7.2 : Pages publiques SSR — fiches formation / école indexables

As a moteur de recherche et acquisition organique,
I want une URL canonique stable et indexable par école / formation (`/formations/{slug}` ou `/ecoles/{slug}`),
So that les pages formations apparaissent sur les recherches "INSA Lyon", "BUT MMI", "Prépa BCPST" (FR46).

**Acceptance Criteria :**

**Given** une fiche école seed (Story 4.1)
**When** je visite `/formations/insa-lyon-genie-biomedical` sans être connecté
**Then** la page est rendue en SSR avec : nom école + ville + photo + description + débouchés + frais + sélectivité brute (anonyme, pas personnalisée) + dates Parcoursup
**And** un CTA "Crée ton compte pour voir ta proba d'admission personnalisée" invite à l'inscription

**Given** des pages liées
**When** je consulte une fiche école
**Then** je vois des liens internes vers les métiers cible (`/metiers/{slug}`) et des écoles similaires (cross-linking)

**Given** la conformité Core Web Vitals
**When** auditée
**Then** mêmes critères que Story 7.1 (TTFB < 1 s, LCP < 2,5 s)

## Story 7.3 : Landing pages long-tail SEO

As a moteur de recherche et acquisition organique,
I want des pages SEO long-tail générées dynamiquement à partir du référentiel (`/devenir-{metier}`, `/{niveau}/quel-bac-pour-{metier}`, `/{niveau}/integrer-{ecole}`),
So that Path-Advisor capte les requêtes spécifiques d'orientation (FR46).

**Acceptance Criteria :**

**Given** le référentiel professions + écoles + formations
**When** je visite `/devenir-infirmiere`
**Then** la page combine la fiche métier + un panel "Quels bacs / formations choisir ?" + des liens vers les écoles cibles + un FAQ structuré

**Given** les variantes par niveau scolaire
**When** je visite `/3eme/quel-bac-pour-technicien-aero`
**Then** le contenu est adapté aux options 3ème (bac pro / général / techno) avec les lycées pro associés à Mehdi

**Given** la stratégie SEO
**When** ces pages sont indexées
**Then** elles utilisent Schema.org `Occupation`, `EducationalOrganization`, `Course`, `FAQPage` markup pour rich snippets
**And** chaque URL a un title + meta description optimisés

## Story 7.4 : Sitemap XML + robots.txt + Schema.org markup

As a moteur de recherche,
I want une sitemap XML auto-générée et un balisage Schema.org strict pour découvrir et indexer toutes les pages publiques,
So that Path-Advisor maximise son indexabilité (FR46).

**Acceptance Criteria :**

**Given** le contenu public (métiers + écoles + landing long-tail)
**When** un crawler accède à `/sitemap.xml`
**Then** la sitemap liste toutes les URLs publiques (métiers, formations, écoles, landings) avec `lastmod` et `priority`
**And** elle est segmentée par type si > 50 000 URLs (sitemap index)

**Given** `/robots.txt`
**When** un crawler le lit
**Then** il autorise l'indexation des pages publiques
**And** il interdit l'indexation des pages applicatives (`/app/*`, `/api/*`, `/admin/*`)

**Given** le balisage Schema.org
**When** un crawler analyse une fiche métier
**Then** le markup `<script type="application/ld+json">` contient un objet `Occupation` complet
**And** Google Rich Results Test valide le markup sans erreur

**Given** la soumission à Google
**When** la sitemap est publiée
**Then** elle est soumise à Google Search Console + Bing Webmaster Tools

## Story 7.5 : Open Graph + Twitter Cards + meta tags

As a réseau social (Instagram, WhatsApp, X, LinkedIn),
I want un preview riche quand un utilisateur partage une page Path-Advisor,
So that le partage social viralise correctement avec image + titre + description (FR46 et viralité organique).

**Acceptance Criteria :**

**Given** chaque page publique Path-Advisor
**When** son URL est partagée sur WhatsApp / Instagram Story / X / LinkedIn
**Then** un preview affiche : titre optimisé + description courte + image Open Graph 1200 × 630 px générée dynamiquement (incluant nom métier ou école)

**Given** la spec Open Graph
**When** je consulte le head HTML d'une page
**Then** je vois `og:title`, `og:description`, `og:image`, `og:url`, `og:type` + Twitter Card équivalents

**Given** des images dynamiques
**When** une page est servie
**Then** une image OG est générée à la volée (Next.js `ImageResponse` API) avec branding Path-Advisor sobre + texte contextuel

## Story 7.6 : Core Web Vitals au vert sur toutes les pages publiques

As a Path-Advisor,
I want des Core Web Vitals au vert sur 100 % des pages publiques indexables,
So that le SEO ne soit pas pénalisé et l'acquisition organique reste forte (NFR-P3 + UX-DR34).

**Acceptance Criteria :**

**Given** une page métier publique
**When** Google PageSpeed Insights audite mobile
**Then** LCP < 2,5 s, FID < 100 ms, CLS < 0,1
**And** Performance score ≥ 80, SEO score ≥ 95

**Given** la mesure continue
**When** la CI s'exécute sur chaque PR
**Then** un job Lighthouse vérifie les Core Web Vitals sur 5 pages publiques de référence
**And** le merge est bloqué si une métrique critique dégrade

**Given** les optimisations
**When** une page est servie
**Then** images en AVIF/WebP avec `srcset` responsive, polices preloadées + `font-display: swap`, JS critique < 200 ko, code-splitting par route Next.js

## Story 7.7 : i18n foundation (français MVP, préparation francophonie)

As a système Path-Advisor,
I want une foundation i18n structurée (clés de traduction extractibles, pas de strings hardcodés),
So that l'expansion francophonie (Belgique, Maroc, Tunisie, Sénégal) en growth soit faisable sans refactor majeur (ADD-11).

**Acceptance Criteria :**

**Given** la stack i18n (next-intl ou next-i18next ou similaire)
**When** je consulte le code
**Then** toutes les strings UI sont dans des fichiers `messages/fr.json` (français MVP unique)
**And** aucun string user-facing n'est hardcodé dans le JSX

**Given** la structure de namespaces
**When** je consulte `messages/fr.json`
**Then** les clés sont organisées par feature (`onboarding.*`, `recos.*`, `parcours.*`, `paywall.*`)
**And** une convention de naming est documentée

**Given** la préparation francophonie growth
**When** un nouveau pays est ajouté
**Then** il suffit de créer `messages/{locale}.json` (ex : `fr-BE`, `fr-MA`) avec les overrides spécifiques (ex : "Parcoursup" → "Equivalent local")
**And** aucun changement de code applicatif n'est requis
