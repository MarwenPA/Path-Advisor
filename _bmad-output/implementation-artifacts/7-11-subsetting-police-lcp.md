# Story 7.11 : Sortir la police du chemin critique LCP (subsetting)

**Status:** done

## 0. Résultat (2026-09-20)

**Toutes les AC satisfaites.** `apps/web/src/app/fonts/inter-vf-latin-fr.woff2` : **26 204 octets contre 48 432 (−46 %)**, servi via `next/font/local` (préchargement + `adjustFontFallback` conservés, `display: "swap"` conservé — la police de marque reste appliquée dès la première visite).

Pipeline (documenté aussi en commentaire dans `layout.tsx`) : `fonttools varLib.instancer` borne l'axe `wght` à 400:700 (48,4 → 36,2 ko — seuls 400/500/600/700 sont utilisés, vérifié par grep des classes Tailwind), puis `pyftsubset` restreint les glyphes au français réel (→ 26,2 ko). Le jeu de caractères a été établi par **inventaire mécanique** du catalogue fr.json + les caractères du référentiel (`·` de « Technicien·ne », `œ`, `«»`, `€`, `°`).

**Zéro régression de glyphe, vérifié contre la source** : `←`, `→`, `Ÿ`, `ﬁ/ﬂ` manquent du subset **mais manquaient déjà du build Google** — les flèches du catalogue s'affichent depuis toujours en police système. Kerning (GPOS `kern`) conservé ; `mark`/`mkmk` élagués (positionnement d'accents combinants, inutile en français précomposé). Delta assumé : le build Google chargeait à la demande des fichiers `latin-ext` (85 ko) pour les caractères hors latin — ils tombent désormais en police système, métriques ajustées.

**Mesures (gunicorn + build de prod, gate uniforme 2500 ms, médiane de 3)** :

| Page | Avant (7.9) | Après | TBT |
|---|---|---|---|
| `/metiers/{slug}` | 2502 | **2316** (runs 2314-2318) | 7 |
| `/formations/{slug}` | 2497 | **2312** | 5 |
| `/`, `/devenir-*`, `/{niveau}/*` | 1955-2346 | 2159-2162 | 3-4 |

**La bimodalité 2105/2500 a disparu** (runs à ±4 ms) — confirmation empirique que la police était toute la variance. L'`assertMatrix` est repliée en un `assert` unique à **2500 ms** pour les 5 pages (AC3) : plus aucune exception dans le gate — et `lighthouse` est passé **SUCCESS en CI réelle** sur ce gate uniforme.

⚠️ **Correction (review légère de clôture)** : la première version de cette section affirmait « 957 tests verts ». C'était un **faux vert** — 957 = 959 − 2 : `layout.test.ts` mockait encore `next/font/google` après le passage à `next/font/local`, ses 2 tests mouraient à l'import, et le résumé `Tests 957 passed` masquait la ligne `Test Files 1 failed` que mon `tail` tronquait. `ci-web` était rouge sur la PR de clôture. Mock corrigé → **121 fichiers / 959 tests passants**, la ligne `Test Files` lue explicitement.

## 1. Constat, mesuré

Le webfont Inter vaut **~400 ms de LCP** sur les deux fiches publiques, et explique toute leur variance. Isolé par expérience en story 7.9 (police basculée temporairement en `display: "optional"`, puis restaurée) :

| Police | LCP `/metiers/{slug}` (3 runs) | Médiane |
|---|---|---|
| `display: "swap"` (actuel) | 2503 / 2105 / 2502 | 2502 ms |
| `display: "optional"` | 2105 / 2105 / 2111 | **2105 ms** |

Configuration actuelle (`apps/web/src/app/layout.tsx`) : `Inter({ subsets: ["latin"], display: "swap" })` via `next/font/google`. Le fichier servi est `48 ko` (`-s.p.woff2`, préchargé) — c'est la **deuxième requête après le document** et de loin le plus gros actif de la page. Sous le modèle 4G lente de Lighthouse (`throttlingMethod: simulate`), son téléchargement décale le repaint du texte.

⚠️ Le diagnostic de Lighthouse désignait `unused-javascript` (250 ms) et `render-blocking-resources` (129 ms). Le bon ordre de grandeur, mais **la mauvaise cause** : ces deux audits pointent les chunks React et vendor, non réductibles. Ne pas repartir de leurs recommandations.

## 2. Pourquoi ne pas simplement mettre `display: "optional"`

Ça marcherait — 2105 ms, variance quasi nulle — mais au prix de la police de marque : avec `optional`, si le fichier n'arrive pas en ~100 ms, le navigateur garde la police système **pour ce chargement** et n'applique Inter qu'aux visites suivantes. Un élève arrivant de Google depuis un mobile sur réseau lent verrait la fiche en police système — or c'est exactement le public cible de l'Epic 7.

Le subsetting obtient le même gain **sans coût visuel** : Inter variable en subset `latin` couvre bien plus de glyphes que le français n'en utilise. Un sous-ensemble restreint aux caractères réellement nécessaires devrait ramener les 48 ko vers ~20-25 ko, sortant la police du chemin critique sans jamais renoncer à l'identité typographique.

## 3. Acceptance Criteria

**AC1** — Le poids du woff2 servi sur les pages publiques est réduit d'au moins 40 % sans perte de glyphe utilisé (accents français, ligatures, `·` du point médian utilisé dans les libellés inclusifs type « Technicien·ne », guillemets français « », apostrophe typographique ’, tirets cadratins —, symboles € et ° présents dans les fiches).

**AC2** — LCP médian < 2500 ms sur les 5 pages de référence avec `display: "swap"` conservé, mesuré via `lhci autorun` (backend gunicorn, build de production).

**AC3** — L'`assertMatrix` de `apps/web/lighthouserc.json` est repliée en un `assert` unique à **2500 ms** pour toutes les pages, et `ci-lighthouse` est vert. Deux comportements vérifiés de lhci : `assertMatrix` lève une erreur si `aggregationMethod` est déclaré au niveau supérieur, et toutes les entrées qui matchent s'appliquent cumulativement (d'où des motifs disjoints).

**AC4** — Aucune régression visuelle : la police reste Inter, le rendu des titres et du corps est inchangé sur les pages publiques et authentifiées.

## 4. Pistes

- Auto-héberger un subset généré (`glyphhanger`, `fonttools pyftsubset`) plutôt que `next/font/google`, en conservant `next/font/local` pour garder le préchargement et l'ajustement automatique des métriques de la police de repli (`adjustFontFallback`, qui évite le décalage de mise en page au swap).
- Vérifier si les poids réellement utilisés justifient la police variable : si seuls 400/500/600/700 sont employés, comparer variable vs statiques subsettés.
- Ne pas casser le préchargement : le fichier actuel est servi avec un `-s.p.` (preload). Le perdre annulerait le bénéfice.

## 5. Note de contexte

On optimise ici une métrique **simulée**, sans métriques utilisateur réelles pour la valider (aucun RUM dans le dépôt — voir story 8.9). L'écart mesuré est un pire cas modélisé sur 4G lente ; l'effet de terrain est probablement moindre. Cette story reste utile — le LCP alimente le classement Google, donc la cible de l'Epic 7 — mais son ordre de priorité devrait être arbitré au regard de la 8.9, qui donnerait enfin de quoi mesurer l'impact réel.
