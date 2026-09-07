# Story 7.9 : LCP — supprimer le render delay sur les fiches publiques

**Status:** ready-for-dev

## 1. Contexte — comment ce défaut a été découvert

La Story 7.6 a posé un gate Core Web Vitals dont l'AC1 exige **LCP < 2,5 s**. Le gate a été livré avec un budget relevé à 3000 ms, justifié à l'époque par « la variance du runner GitHub partagé ». **Cette justification était fausse**, et deux erreurs l'ont rendue invisible :

1. `lighthouserc.json` ne déclarait pas `aggregationMethod`, et le défaut de LHCI est `optimistic` — l'assertion passe si **la meilleure** des 3 runs passe. Le gate n'a donc jamais mesuré ce qu'on croyait.
2. La CI servait le backend via `manage.py runserver` (mono-process), ce qui ajoutait un surcoût réel — mais mineur devant la vraie cause.

Après correction des deux (gunicorn en CI + `aggregationMethod: "median"`), mesure locale sur machine rapide et backend rapide :

| Page | LCP (3 runs) | Médiane |
|---|---|---|
| `/metiers/technicien-aeronautique` | 2797 / 2946 / 2799 ms | **2798 ms** |
| `/formations/lycee-pro-aviation` | 2500 / 2497 / 2502 ms | **2500 ms** |

Ce n'est ni du bruit, ni le runner : c'est un coût réel et reproductible de la page.

## 2. Diagnostic (déjà fait, à ne pas refaire)

Décomposition du LCP sur `/metiers/technicien-aeronautique` :

- TTFB : **4 ms** (mesure Lighthouse) — le backend n'est pas en cause
- FCP : **757 ms** — le premier paint est sain
- TBT : **41 ms** — pas un problème de JS bloquant
- Score performance : **0,96** — excellent, seule la métrique LCP brute échoue
- **Render delay : 2344 ms** ← tout le problème est là

L'élément LCP est un `<p class="text-body text-text">`. Vérification faite : cette classe **n'apparaît pas dans le HTML initial** (`curl` de la page), alors que le texte de la description est bien présent dans le payload RSC. Autrement dit : le contenu visible de la fiche est produit par un Client Component (`apps/web/src/app/metiers/[slug]/FicheMetierClient.tsx`, hérité de la Story 7.1), et ne peint donc qu'après le chargement + l'hydratation du JS.

Sur une page dont la raison d'être est l'indexation et les Core Web Vitals, faire dépendre le contenu principal de l'hydratation est le défaut de fond.

## 3. Objectif

Faire peindre le contenu principal des fiches publiques côté serveur, pour ramener le LCP sous 2500 ms, puis resserrer le budget du gate.

## 4. Acceptance Criteria

**AC1** — Sur `/metiers/{slug}` et `/formations/{slug}`, l'élément LCP est présent dans le HTML initial (vérifiable au `curl`, sans exécution de JS).

**AC2** — LCP médian < 2500 ms sur les 5 pages de référence, mesuré via `lhci autorun` avec `aggregationMethod: "median"` et un backend gunicorn (les conditions du gate actuel).

**AC3** — Le budget LCP de `apps/web/lighthouserc.json` est ramené de 3000 à **2500 ms** dans la même PR que le correctif, et `ci-lighthouse` est vert.

**AC4** — Aucune régression fonctionnelle sur l'affichage authentifié des fiches (score, niveau de confiance, signaux contributifs, drawer) : ce sont les seules parties qui ont légitimement besoin d'être clientes.

## 5. Piste d'implémentation

Le principe : ne garder en Client Component que ce qui a réellement besoin d'interactivité, et rendre le reste côté serveur.

- `FicheMetierClient` / `FicheMetier` enveloppent aujourd'hui l'ensemble de la fiche. À découper : contenu statique (titre, description, missions, débouchés, salaire, formations) en Server Components ; interactivité (accordéon mobile, drawer des signaux, `AdmissionStatPoller`, boutons de signalement) en îlots clients.
- Attention : `MetierPageBody.tsx` (ajouté lors des correctifs de review) isole déjà les `searchParams` dans un `<Suspense>` pour permettre l'ISR — ne pas défaire ça, l'articuler avec.
- Vérifier l'effet sur `/formations/{slug}` aussi : sa médiane est à 2500 ms tout juste, `FicheEcole` est déjà un composant serveur mais mérite une mesure après coup.

## 6. Vérification attendue

Ne pas se fier au build ni aux tests unitaires : mesurer. `lhci autorun` en local avec gunicorn + build de production, puis confirmer en CI réelle via `gh run watch`. La leçon de la 7.6 est que ce défaut a survécu à des dizaines de runs verts parce que l'agrégation choisie ne mesurait pas ce qu'on croyait.

## 7. Notes

- Le budget reste à **3000 ms** en attendant cette story. Ce n'est pas un relâchement déguisé : combiné à `aggregationMethod: "median"`, le gate est aujourd'hui plus strict qu'il ne l'a jamais été (auparavant : meilleur des 3 à 3000 ms). Il capture les régressions au-delà de la ligne de base actuelle, mais pas l'écart de 300-500 ms qui nous sépare de la cible produit.
- Aucun RUM n'existe dans le dépôt (PostHog différé), donc rien ne surveille la bande 2,5-3,0 s en production.
