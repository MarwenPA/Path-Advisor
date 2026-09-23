# Story 8.9 : Métriques utilisateur réelles (RUM) sur les Core Web Vitals

**Status:** review

## 0. Résultat (2026-09-20)

**AC1-AC4 livrées ; AC5 est datée par nature** (réexamen des budgets après 2-4 semaines de données — un rappel est posé dans la section AC5).

**Backend** — nouvelle app `apps/telemetry` : `POST /api/v1/rum/vitals/` (AllowAny, throttle `rum_ingest` 60/min/IP, `authentication_classes = []` pour que le beacon d'un élève connecté ne soit jamais rattachable à sa session) et `GET /api/v1/admin/rum/summary/` (path_admin, p75 rang-le-plus-proche par métrique × type de page, segmenté device/connexion — fenêtre 28 j par défaut, 90 j max, alignée CrUX). Rétention : commande `prune_rum_vitals` (90 j). **13 tests**, dont un qui épingle le schéma : la table n'a *aucune colonne* utilisateur/IP/URL — la vie privée est par construction, pas par politique. `mypy apps/telemetry` : 0 erreur.

**Frontend** — collecteur hors React : `src/instrumentation-client.ts` (convention Next) charge `src/lib/telemetry/rum.ts` **à l'idle du navigateur, après `load`** — les PerformanceObservers de `web-vitals` sont bufferisés, donc l'abonnement tardif capte quand même LCP/FCP/TTFB. `pathnameToPageType` est un mapping fermé des 5 types de pages publiques ; tout le reste (espace authentifié inclus) n'est **jamais** mis en file. Batch unique flushé sur `visibilitychange`/`pagehide` via `fetch(keepalive, credentials: "omit")` — pas de `sendBeacon`, qui ne porte pas `application/json` sans ennuis CORS. **17 tests**, dont : un chemin authentifié n'est jamais rapporté, le payload ne contient jamais le pathname, pas de double-envoi.

⚠️ **Cette architecture est la seconde — la première s'est fait attraper par le gate qu'elle devait calibrer.** La v1 était un composant client (`RumReporter`) monté dans le layout racine : une frontière cliente au layout racine met son chunk sur le chemin critique de *toutes* les pages, et `ci-lighthouse` a mesuré **+~40 ms de LCP simulé** sur `/metiers/{slug}` (2538/2543/2540 ms, grappe ±5 ms — pas du bruit), au-dessus du budget 2500. Relever le budget était exclu (leçon de l'Epic 7). La v2 coûte **zéro octet critique**, vérifié dans `build-manifest.json` : les chunks RUM (~9,6 ko au total, `web-vitals` inclus) sont absents de `rootMainFiles`, chargés à l'idle. L'instrument de mesure ne doit pas fausser la mesure.

**Forensique d'une expérience confondue (à garder — c'est la leçon de la story).** La première vérification vivante de la v2 a donné zéro ligne en base, contre 9 pour la v1. J'ai d'abord accusé la fenêtre d'idle (deadline 5 s « trop tardive »), resserrée à 1,2 s — zéro encore. Un flush forcé post-abonnement (bissection) — zéro toujours. La vérité est venue de Chrome headless piloté en direct avec sa console : `__RUM_BOOT__` ✓, `__RUM_INIT__` ✓, puis **blocage CORS** — mes probes v2 tournaient sur le port **3200**, absent de `CORS_ALLOWED_ORIGINS`, quand la v1 « 9 lignes » tournait sur **3000**. J'ai comparé deux versions de code dans deux environnements : la variable était le port, pas l'architecture — qui fonctionnait probablement depuis la première version. Ma « preuve » intermédiaire (`grep timeout:5e3` dans les chunks) était en outre un faux positif possible, ce littéral étant générique ; seuls des marqueurs uniques + la console du navigateur ont tranché. Le commentaire mensonger laissé entre-temps dans `instrumentation-client.ts` a été réécrit avec la cause réelle.

Preuve finale sur l'origine autorisée (port 3000, build de prod, Chrome headless) : **FCP/LCP/TTFB en base** malgré l'abonnement tardif — les observers bufferisés font leur travail ; CLS/INP absents à juste titre (session sans interaction ni shift). Note opérationnelle : le beacon voyage sous le **même régime CORS** que tous les appels API du front (`NEXT_PUBLIC_API_URL`) — aucune configuration nouvelle requise en production.

**Vérifié en bout-en-bout par un vrai navigateur** (leçon de l'Epic 7 : le build qui passe ne prouve rien) : Chrome piloté par Lighthouse sur la stack docker de dev → 9 lignes en Postgres avec `page_type=metier_fiche`, device `mobile`, connexion `4g`. Le flux complet — mesure web-vitals, file, flush pagehide, CORS, validation d'enum, écriture — fonctionne sans intervention manuelle.

Corrections en cours de route, consignées : mon premier test de p75 attendait 1000 pour `[1000,1000,2000]` — **le code avait raison** (rang-le-plus-proche de 3 échantillons = le 3ᵉ) ; et le test de throttle devait épingler le taux sur la classe (DRF fige `THROTTLE_RATES` à l'import — le commentaire de `settings/test.py` le disait déjà).

**Page RGPD** mise à jour (finalité « Mesure de performance technique », formulée pour un adolescent : ni identifiant, ni IP, ni URL complète, purge à 90 j).

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
