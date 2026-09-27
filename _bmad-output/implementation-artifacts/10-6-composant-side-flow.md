# Story 10.6 — Composant `SideFlow` (confirmations critiques non-bloquantes)

**Epic 10 — Fast-follow post-MVP · UX-DR18 · Statut : review**

As a développeur Path-Advisor, I want un composant `SideFlow` réutilisable pour les
confirmations critiques qui ne bloquent pas l'exploration en cours, So that les
flows non-bloquants soient gérés proprement (UX-DR18).

## Ce qui est livré

- **`components/ui/side-flow.tsx`** — composant générique : bandeau persistant
  `role="status"` / `aria-live="polite"` (jamais `dialog` : pas de focus trap,
  pas de scroll lock — l'exploration reste possible, AC1), positions `top`
  (in-flow, sous la nav) et `bottom` (fixe, au-dessus de la tab bar mobile
  64px, `bottom-16 lg:bottom-0`), CTA secondaire optionnel, zone de feedback
  inline, et **toast de résolution** : quand `open` passe de vrai à faux avec
  `resolvedMessage`, le bandeau disparaît et un toast confirme (AC3). Un premier
  rendu fermé n'émet jamais de toast (la transition doit avoir été vue).
- **`components/ui/toast.tsx`** — `useToast` + `<Toast>` extraits des copies
  identiques de `ReportErrorButton` et `ReviewRequestButton` (3.7/3.8), les deux
  boutons migrés dessus.
- **`hooks/use-current-user.ts`** — lecture partagée de `/auth/user/` avec
  `pollWhile` conditionnel, en fetch + `setTimeout` chaîné (patron
  `AdmissionStatPoller`, ADD-8). **Leçon (attrapée par la gate Lighthouse)** :
  la première version utilisait `useQuery`, et webpack a replié query-core
  dans le chunk commun que les pages publiques chargent — +11,5 KB et
  +200 ms de LCP sur les landings SEO (2560 ms vs budget 2500, baseline
  verte 2353). Diagnostic par diff des rapports LHCI uploadés (bootup
  +150 ms, main-thread +268 ms) puis diff des chunks entre builds main et
  branche. Un composant du layout authentifié ne doit jamais taxer le
  bundle public.
- **`components/features/auth/parental-consent-sideflow.tsx`** — l'instance 1.4,
  remplace `LimitedModeBanner` (supprimé) dans le layout authentifié. Poll 30 s
  (ADD-8 : pas de WebSocket MVP) tant que `pending_parental_consent`.
- **API : `parental_consent_state`** sur `GET /api/v1/auth/user/`
  (`pending`/`granted`/`expired`/`none`, `null` hors pending) — l'ancien bandeau
  keyait sur `status` seul et proposait « renvoyer l'email » dans des états où
  l'endpoint répond 404 (consentement accordé ou fenêtre 60 j expirée).
- **i18n** : namespace `sideFlow` (fr.json) + ajout à `AUTH_ONLY_NAMESPACES`
  (garde perf LCP pages publiques) ; copies conformes au lint de ton
  (« Ton parent reçoit l'email — tu peux continuer pendant qu'on vérifie »,
  « Ton compte est entièrement actif maintenant »).

## Décisions

- **Résolution = transition d'état, pas action utilisateur.** Le toast est dans
  le composant générique (chaque instance future l'a gratuitement), déclenché
  uniquement sur une transition ouverte→fermée réellement observée.
- **CTA par état** : `pending` → « Relancer mon parent » (429 rate-limit 1/h
  affiché calmement) ; `granted` → copie « confirme ton adresse email », sans
  CTA de relance (rien à renvoyer au parent) ; `expired`/`none` → renvoi vers
  /support. Note : la connexion exigeant l'email vérifié, l'état `granted` est
  en pratique inatteignable pour un utilisateur connecté (grant + email vérifié
  ⇒ `active` immédiat) — la branche reste servie par l'API et testée, par
  défense.
- **Pas de portal pour le toast** : un message éphémère par flow, rendu local —
  consigné ; un vrai gestionnaire de toasts empilés viendra si un besoin réel
  l'exige.
- **Migration des autres lecteurs one-shot de `/auth/user/`** (`mfa-banner`,
  `ProgressionModule`, `outreach-section`, `onboarding-step-2`) vers
  `useCurrentUser` : hors périmètre, consigné comme cleanup candidat.
- Nettoyage bookkeeping embarqué : lignes 7-1…7-7 du sprint-status repassées à
  `done` (restées `in-progress` après la re-clôture de l'epic 7 du 20/09).

## Résultats

- **Tests** : API fast lane **1606** passed (dont 4 nouveaux sur
  `parental_consent_state`) ; lane RLS Postgres locale **155** passed ; web
  **1035** passed (dont 4 `side-flow`, 6 `parental-consent-sideflow`) ; tsc,
  eslint, ruff propres ; mypy : zéro nouvelle erreur (3 préexistantes
  identiques sur `serializers.py`).
- **Preuve live** (stack dev, runtimes redémarrés) : inscription mineur 13 ans
  avec email parent → vérification email (clé Mailpit) → login →
  `GET /auth/user/` : `status=pending_parental_consent, state=pending` →
  relance parent **200** (email « votre enfant attend toujours votre réponse »
  dans Mailpit) → seconde relance **429** → décision parent `granted` par token
  → `GET /auth/user/` : `status=active, state=null, is_fully_active=true` —
  la transition exacte que le poll du bandeau convertit en disparition + toast.
  Compte de preuve conservé : `sideflow-live-106@test.local`.
