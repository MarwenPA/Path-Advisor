# Story 7.10 : Dettes issues de la review Epic 7 (i18n FicheMetier + école désactivée)

**Status:** ready-for-dev

Deux dettes identifiées et **délibérément non traitées** pendant les correctifs de review, pour éviter des changements risqués en fin de cycle. Elles sont indépendantes l'une de l'autre et peuvent être découpées.

---

## Partie A — Migrer `FicheMetier` vers next-intl

### Constat

La Story 7.7 revendiquait « aucune string user-facing hardcodée » sur les pages publiques migrées. La review a montré que c'était faux d'un cran : les pages avaient bien été migrées, mais les composants qu'elles **rendent** restaient intégralement en français codé en dur. `FicheEcole` a été migré depuis (correctifs de review) ; **`FicheMetier` ne l'est pas.**

C'est la dernière grosse poche de français en dur sur les pages publiques : `apps/web/src/components/professions/FicheMetier.tsx` (~650 lignes) + ses sous-composants (`SignauxDrawer`, listes de prérequis, libellés d'onglets « Pour qui » / « Comment y aller » / « Infos pratiques » / « Signaux contributifs », « Passions / Valeurs / Spécialités / Études / Compétences / Qualités », plusieurs `aria-label`).

Non fait pendant la review : ~650 lignes, 29 tests existants, et un couplage entre les clés de section et la logique d'accordéon — une migration à moitié faite aurait été pire que pas de migration.

### Acceptance Criteria

**AC1** — Aucune string user-facing hardcodée dans `FicheMetier.tsx` et ses sous-composants ; tout passe par `useTranslations` sous un namespace `ficheMetier.*` dans `apps/web/messages/fr.json`.

**AC2** — La vérification est faite par **grep systématique** (littéraux JSX, `aria-label`, `alt`, `title`, `placeholder`, messages d'erreur), pas par relecture — c'est précisément l'écart qui a produit la fausse revendication de la 7.7.

**AC3** — Les 29 tests existants passent, migrés vers `renderWithIntl` (`apps/web/src/test/render-with-intl.tsx`) là où nécessaire.

**AC4** — La pluralisation éventuelle utilise la syntaxe ICU, pas de `x > 1 ? "s" : ""` en dur (cf. `docs/i18n-conventions.md`).

### Attention

Cette story croise probablement la **Story 7.9** (LCP / render delay), qui prévoit de découper `FicheMetier` en Server Components + îlots clients. **Coordonner l'ordre** : faire 7.9 d'abord évite de migrer en i18n du code qui va être restructuré, ou inversement. À arbitrer au lancement.

---

## Partie B — Signaler une école désactivée dans « Mes paris »

### Constat

Les correctifs de review ont ajouté `is_active=True` sur toutes les surfaces **publiques** des écoles (détail SEO, flux du sitemap, écoles similaires, parcours). Deux vues authentifiées ont été **volontairement laissées non filtrées** :

- `SchoolDetailView` (`apps/api/apps/schools/views.py`)
- `MesParisListView` (idem)

Raison : un favori d'élève pointant vers une école depuis désactivée doit rester visible dans `/mes-paris` et sa fiche ne doit pas renvoyer 404. Filtrer aurait fait disparaître silencieusement un favori, ou cassé le clic — un mauvais échange pour corriger une fuite SEO.

Mais en l'état, **l'élève n'a aucun signal** que l'établissement n'est plus au catalogue : il voit une fiche normale, peut continuer à la considérer dans son projet d'orientation, et peut fonder une décision sur une donnée périmée. Sur un produit d'orientation scolaire, c'est un vrai problème produit.

### Acceptance Criteria

**AC1** — Le sérialiseur authentifié des écoles expose l'information de désactivation (ex. `is_active`, ou un champ dédié `is_referenced`) — et **seulement** sur les endpoints authentifiés, jamais sur les sérialiseurs publics SEO.

**AC2** — Dans `/mes-paris` et sur la fiche école authentifiée, une école désactivée porte une mention explicite et compréhensible par un adolescent (ex. « Cet établissement n'est plus référencé sur Path Advisor »), sans jargon.

**AC3** — Le favori reste consultable et supprimable ; aucune régression de la Story 4.8 (favoris / mes paris).

**AC4** — Les probabilités d'admission ne sont plus affichées pour une école désactivée (une prédiction sur un établissement retiré du référentiel n'a pas de sens), ou sont accompagnées d'un avertissement clair.

**AC5** — Accessibilité : la mention n'est pas portée par la seule couleur (RGAA), et est annoncée aux lecteurs d'écran.
