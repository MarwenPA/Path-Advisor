# Story 7.11 : Sortir la police du chemin critique LCP (subsetting)

**Status:** ready-for-dev

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
