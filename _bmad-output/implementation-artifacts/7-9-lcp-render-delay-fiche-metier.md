# Story 7.9 : LCP — supprimer le render delay sur les fiches publiques

**Status:** review

## 0. Résultat (2026-09-08)

### La cause réelle était une régression introduite par le correctif `revalidate` de la review

Le correctif de la review avait déplacé tout le corps de la page dans un composant client derrière un `<Suspense fallback={null}>` pour libérer l'ISR. Comme ce composant lisait `useSearchParams`, Next ne pouvait pas le prérendre statiquement et servait le fallback — **c'est-à-dire rien**. L'ISR était bien obtenu (`●` dans le manifeste) mais au prix d'un HTML vide de son contenu. Vérifié : zéro occurrence de la classe de l'élément LCP dans le HTML servi.

Correctif : `useSearchParams` remplacé par une lecture de `window.location.search` via `useSyncExternalStore` (snapshot serveur `""`), et suppression de la frontière Suspense. Le HTML prérendu est désormais **toujours la fiche anonyme complète** ; l'hydratation ré-affiche une fois avec les vrais paramètres pour les élèves arrivant de `/mes-metiers`. Un abonnement `popstate` a été ajouté pour le seul cas qui ne remonte pas le composant (précédent/suivant entre deux variantes de query de la même URL).

Second levier : `SignauxDrawer`, `ReportErrorButton` et `ReviewRequestButton` chargés en `next/dynamic({ssr:false})` — ce sont des composants d'interaction pure, hors chemin critique.

### Mesures (gunicorn + build de production, médiane de 3)

| Page | LCP avant | LCP après | TBT avant | TBT après |
|---|---|---|---|---|
| `/metiers/{slug}` | ~3045 | **2502** | 278 | **46** |
| `/formations/{slug}` | ~2500 | **2497** | — | 42 |
| `/` | — | 1957 | — | 40 |
| `/devenir-*` | — | 1955 | — | 41 |
| `/{niveau}/quel-bac-*` | — | 2346 | — | 42 |

Propriétés vérifiées : contenu présent dans le HTML servi ; HTML avec `?score=82&confidence=high` **identique octet pour octet** à la version anonyme (aucun score d'élève ne peut être figé dans le cache ou un snippet SERP) ; ISR préservé (`●`, routes présentes dans `.next/prerender-manifest.json`). Lint 0 erreur, typecheck, format, **951 tests**, build : verts.

### AC3 partiellement satisfaite — et pourquoi

Les deux fiches restent bimodales : 2105 ms **ou** ~2500 ms selon que la police arrive à temps. Cause isolée par expérience — police basculée temporairement en `display: "optional"`, puis restaurée :

| Police | LCP `/metiers` (3 runs) | Médiane |
|---|---|---|
| `display: "swap"` (actuel) | 2503 / 2105 / 2502 | 2502 |
| `display: "optional"` | 2105 / 2105 / 2111 | **2105** |

Le webfont Inter (48 ko, subset latin, préchargé) vaut donc **~400 ms de LCP** et explique toute la variance. À noter : `unused-javascript` (250 ms) que Lighthouse désignait porte sur les chunks React et vendor — non réductibles ; le diagnostic de l'outil pointait le bon ordre de grandeur mais la mauvaise cause.

`display: "optional"` réglerait le problème, mais au prix de la police de marque à la première visite sur connexion lente — décision de design, non technique, donc **non prise ici**. Le levier propre est le subsetting de la police (même gain, aucun coût visuel) : story **7.11**.

En conséquence l'`assertMatrix` est conservée, mais **resserrée** : 2600 ms sur les deux fiches (contre 3000 avant), 2500 ms strict sur les trois autres pages. L'exception rétrécit à mesure que le défaut rétrécit. `/formations` sortait à 2497 ms contre un seuil de 2500 — 3 ms de marge n'est pas une garantie, d'où son inclusion dans l'exception plutôt qu'un vert de façade.

À corriger avec la story 7.11 : replier la matrice en un `assert` unique à 2500 ms.

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

**AC3** — L'exception ciblée de `apps/web/lighthouserc.json` est **supprimée** dans la même PR que le correctif, et `ci-lighthouse` est vert.

Concrètement : le fichier utilise aujourd'hui un `assertMatrix` à deux entrées mutuellement exclusives —

| Entrée | Pages | Budget LCP |
|---|---|---|
| `^http://localhost:3000/(?!metiers/\|formations/)` | `/`, `/devenir-*`, `/{niveau}/quel-bac-pour-*` | **2500 ms** (cible produit) |
| `^http://localhost:3000/(metiers\|formations)/` | `/metiers/{slug}`, `/formations/{slug}` | **3000 ms** (plafond provisoire, ce défaut) |

Une fois le render delay corrigé, les deux entrées doivent être fusionnées en un `assert` unique à 2500 ms pour toutes les pages. Deux pièges vérifiés dans la source de `@lhci/utils` : `assertMatrix` **interdit** `aggregationMethod` au niveau supérieur (il doit figurer dans chaque entrée), et **toutes** les entrées qui matchent s'appliquent cumulativement — d'où des motifs strictement disjoints plutôt qu'un fourre-tout suivi d'une surcharge, qui ne fonctionnerait pas.

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
