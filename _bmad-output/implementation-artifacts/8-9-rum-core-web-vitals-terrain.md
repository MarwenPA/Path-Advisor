# Story 8.9 : Métriques utilisateur réelles (RUM) sur les Core Web Vitals

**Status:** ready-for-dev

## 1. Le manque

Le projet pilote sa performance sur une métrique **entièrement simulée**. `apps/web/lighthouserc.json` utilise `throttlingMethod: "simulate"` : Lighthouse prend une trace non throttlée et **modélise** ce qui se passerait sur une 4G lente. C'est utile comme garde-fou anti-régression, mais ça ne dit rien de ce que vivent les utilisateurs.

Conséquences concrètes observées pendant l'Epic 7 :

- Le budget LCP a été relevé de 2500 à 3000 ms en story 7.6 sur la foi d'une hypothèse (« variance du runner ») qui s'est révélée **fausse** — c'était un vrai défaut de rendu côté client. Personne ne pouvait le trancher, faute de données de terrain.
- Les deux fiches publiques oscillent aujourd'hui entre 2105 et ~2500 ms selon l'arrivée du webfont (story 7.11). On ne sait pas laquelle de ces deux valeurs correspond à la réalité du terrain, ni pour quelle proportion des visiteurs.
- La documentation de la 7.6 promettait « à surveiller via de vraies métriques utilisateur ». **Rien ne surveille cette bande.** PostHog a été explicitement différé (voir l'en-tête de `infra/docker-compose.yml`).

Autrement dit : on a un gate CI, mais aucun thermomètre.

## 2. Objectif

Collecter les Core Web Vitals réels (LCP, CLS, INP, TTFB) depuis les navigateurs des visiteurs, les segmenter, et s'en servir pour calibrer les budgets CI sur des faits plutôt que sur des hypothèses.

## 3. Acceptance Criteria

**AC1** — Les Core Web Vitals réels sont collectés côté client sur les pages publiques (`/`, `/metiers/{slug}`, `/formations/{slug}`, `/devenir-*`, `/{niveau}/quel-bac-*`) via l'API `web-vitals` ou l'équivalent natif Next (`useReportWebVitals`).

**AC2** — Les mesures sont segmentables par **type de page**, **type d'appareil** et **type de connexion** (`navigator.connection.effectiveType` quand disponible) — sans quoi une médiane globale masquerait précisément la population qu'on cherche à protéger : les élèves sur mobile et réseau lent.

**AC3** — Le p75 (le seuil que Google utilise pour son classement) est consultable par page et par segment.

**AC4 — RGPD, non négociable.** L'application traite des données de **mineurs**. La collecte doit être anonyme et sans identifiant utilisateur, sans cookie de suivi, agrégée, et couverte par la documentation de conformité existante (`audit-events.md`, page RGPD `/legal/rgpd`). Aucune mesure de performance ne doit pouvoir être rattachée à un élève identifiable. Si la solution retenue implique un tiers, elle doit passer par la validation de l'équipe Privacy — pas par défaut.

**AC5** — Une fois 2 à 4 semaines de données accumulées, les budgets de `lighthouserc.json` sont **réexaminés sur cette base** : soit resserrés si le terrain est meilleur que la simulation, soit assumés tels quels avec les chiffres à l'appui. Cette réévaluation fait partie de la story, pas d'un « plus tard ».

## 4. Pourquoi c'est dans l'Epic 8

L'Epic 8 porte la continuité temporelle et l'observabilité produit. Cette story y est rattachée plutôt qu'à l'Epic 7 parce qu'elle dépasse le SEO : les mêmes données serviront à arbitrer les priorités de performance sur l'espace authentifié.

## 5. Dépendance à noter

La story **7.11** (subsetting de la police) et celle-ci s'éclairent mutuellement. Si le RUM montre que la quasi-totalité des visiteurs sont sur de bonnes connexions, le sujet police perd en urgence ; s'il montre l'inverse, il devient prioritaire. Faire 8.9 d'abord permettrait de trancher 7.11 sur des faits — mais 7.11 est peu coûteuse et sans coût visuel, donc l'ordre n'est pas bloquant.
