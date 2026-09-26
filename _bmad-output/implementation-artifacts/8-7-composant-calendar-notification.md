# Story 8.7 — Composant `CalendarNotification`

Statut : review · Epic 8 (continuité temporelle & notifications) · 2026-09-26

## 1. User Story

As a développeur Path-Advisor, I want un composant `CalendarNotification` réutilisable pour toute notification calée sur le calendrier Parcoursup, So that le pattern « calendrier sans urgence » soit cohérent (UX-DR17 + UX-DR28).

ACs (epic-8) : props (`jalon`, `daysUntil`, `recommendedActions[]`) ; titre factuel + description calme + checklist non-bloquante ; AUCUN compte à rebours visuel agressif ; copy bannissant URGENT/DERNIÈRE CHANCE/etc. ; réutilisation email (8.3) et DeltaRecap (8.6) — « seul le rendering layer change ».

## 2. Décisions de périmètre

1. **« Le même composant » = la source unique de copy + la forme de données, pas un module de code unique.** Un email HTML Django et une app React ne peuvent pas exécuter le même fichier ; ce que l'AC exige (« seul le rendering layer change »), 8.3/8.6 l'ont déjà construit : `milestone_copy.py::MILESTONE_COPY` est LA source (subject/intro/checklist/cta), et la forme `{jalon, days_until, recommended_actions[], cta}` est le contrat. Deux renderers : le template email `parcoursup_milestone.{txt,html}` (8.3) et — ce que cette story crée — le composant React `CalendarNotification`. Toute nouvelle copy passe par `MILESTONE_COPY`, où le lint 8.3 la contraint automatiquement.
2. **Cette story formalise le renderer React** : extraction de la carte jalon rendue inline par `DeltaRecapInterstitial` (8.6) vers `components/notifications/CalendarNotification.tsx` avec les props de l'AC. Le badge « dans X jours » est un texte statique neutre (token muted) — pas de timer, pas de `setInterval`, pas d'`aria-live`, pas de rouge : l'anti-compte-à-rebours est un TEST (absence de minuterie + snapshot des classes du badge), pas une intention.
3. **Le lint de copy reste backend** (8.3 sur `MILESTONE_COPY` rendu ; 8.6 sur les cartes) — le composant n'écrit aucune phrase. Côté front, le test vérifie : rendu verbatim des strings, checklist en liste non-bloquante (pas de checkbox obligatoire, pas d'état de complétion), CTA unique.
4. Consommateurs actuels : DeltaRecap (in-app). L'email 8.3 reste sur son template Django (même source de copy). Un futur écran « calendrier » (Epic 9+) réutilisera ce composant tel quel.

## 3. Périmètre technique

- `apps/web/src/components/notifications/CalendarNotification.tsx` (+ test) — props `{ jalon, daysUntil, body, recommendedActions, ctaLabel, ctaUrl, onCtaClick? }`.
- `DeltaRecapInterstitial.tsx` : la carte `kind === "parcoursup_milestone"` délègue au composant (déduplication du rendu inline).
- Aucun changement backend (contrat déjà servi par `delta_recap._calendar_card`).

## 4. Résultats (implémentation)

**Livré.**

- `components/notifications/CalendarNotification.tsx` : le renderer React unique du pattern « calendrier sans urgence » — props `{jalon, daysUntil, body, recommendedActions[], ctaLabel, ctaUrl, onCtaClick?}`, badge « dans X jours » statique (token muted, accord 0/1/n : « aujourd'hui » / « dans 1 jour » / « dans 18 jours »), checklist en liste simple (jamais des checkboxes), CTA unique. Aucune phrase écrite par le composant — tout vient de `MILESTONE_COPY` via la carte 8.6.
- `DeltaRecapInterstitial` : la carte `kind === "parcoursup_milestone"` délègue au composant (rendu inline dédupliqué) ; les autres kinds gardent leur layout local (chip stat).
- **Tests** (6, `CalendarNotification.test.tsx`) : strings verbatim + checklist non-bloquante (`queryByRole("checkbox")` vide) ; CTA unique + forward du clic ; **anti-compte-à-rebours exécutable** — badge sans `aria-live`, classes sans `red|destructive|animate|pulse`, `setInterval` jamais appelé au rendu ; accord français paramétré [0, 1, 18]. Suite web complète **996 passed** (126 fichiers) ; tsc 0 ; eslint 0 sur les fichiers touchés. Le lint de copy reste backend (8.3 sur `MILESTONE_COPY`, 8.6 sur les cartes) — consigné §2 : « le même composant » = source de copy + forme de données uniques, deux rendering layers (template email Django 8.3, ce composant React).
- **Preuve live** (stack dev, session réelle) : SSR `/accueil` → interstitiel avec la carte jalon rendue par `CalendarNotification` (`calendar-days-until`, « dans 18 jours », « la plateforme ouvre le 14 octobre ») aux côtés des cartes réponse/nouvelles-écoles.
- **Piège attrapé (3e du genre, famille colima/file-watching)** : le runserver pa-api gardait l'ancien module `models` en mémoire → `ImportError: cannot import name 'DeltaRecapCursor'` en 500 sur l'endpoint alors que le fichier du conteneur était frais (l'import paresseux de la vue relisait `delta_recap.py` neuf contre un `models` vieux). Diagnostic : grep dans le conteneur = fichier à jour → c'est le process ; fix : `docker compose restart api`. Même famille que `.next` stale (8.6) et le worker Celery (8.5) : **sur colima, après tout changement de code, redémarrer le runtime concerné avant toute preuve live.**
- Noté au passage : un jalon campagne `demo` (14 oct. 2026, J-18) existe en dev en plus de mon `proof-8-6` — seed de l'utilisateur, non touché.
