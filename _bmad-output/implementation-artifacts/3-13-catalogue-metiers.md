# Story 3.13: Catalogue de tous les métiers — repli quand pas encore de recos

**Epic:** 3 — Recommandation Vocationnelle (réouverture ciblée)
**Status:** done
**Story Key:** `3-13-catalogue-metiers`
**Estimation:** S (small) — le référentiel `Profession` (Story 3.2) existe déjà avec 52 métiers riches et seedés (`seed_professions`), la fiche détail `/metiers/[slug]` existe déjà (Story 3.5/3.12). Cette story n'ajoute qu'un endpoint de LISTE (jamais créé — seul le detail existe) + une page catalogue + un bouton de repli sur `/accueil`.

> Demandé en session live (2026-09-05) : sur `/accueil`, quand "Tes métiers" n'a aucune recommandation (profil pas encore assez rempli), il n'y a aujourd'hui **aucune action possible** dans ce module à part le texte "Tes recommandations arrivent dès que ton profil est prêt." — l'élève ne peut pas explorer le référentiel en attendant. Le user a explicitement demandé de démarrer avec les métiers déjà seedés (52, dépasse largement les "30 d'exemple" demandés) et de reporter le scraping/l'extension du référentiel à une story dédiée future.

---

## 1. User Story

**As an** élève dont le profil n'est pas encore assez rempli pour avoir des recommandations scorées,
**I want** pouvoir quand même parcourir le catalogue complet des métiers du référentiel,
**So that** je ne sois jamais bloqué devant un module vide sans rien à faire.

---

## 2. Scope decisions

- **Backend** : `Profession` (52 lignes actives en local après `seed_professions`) a déjà un serializer public (`ProfessionPublicSerializer`, detail) mais **aucun endpoint de liste public** — seul `AdminProfessionListView` (staff) existe. Ajouter :
  - `ProfessionCatalogSerializer` — version allégée pour une liste (id, slug, name, sector, description tronquée côté frontend si besoin, median_salary_eur). Ne PAS renvoyer `daily_routine`/`requirements_json`/`prospects_text`/`signals_json` dans la liste — poids inutile, ces champs restent sur le detail existant.
  - `PublicProfessionListView` — `GET /api/v1/professions/`, mêmes permissions que le detail existant (`IsAuthenticatedAndActive, IsStudent`), paginé (réutilise `_ProfessionPagination`, 50/page — suffisant aujourd'hui, prépare la croissance du référentiel).
  - URL : `path("professions/", PublicProfessionListView.as_view(), name="public-list")` dans `apps/professions/urls.py`, avant le pattern à slug (pas de collision réelle, Django distingue par présence/absence de segment).
- **Frontend** :
  - `fetchProfessions()` dans `lib/api/professions.ts` — `GET /api/v1/professions/`, retourne `{ results, count, next }` (forme DRF `PageNumberPagination` standard).
  - Nouvelle page `apps/web/src/app/(authenticated)/metiers/page.tsx` — grille de cartes (nom, secteur, salaire médian si connu, début de description tronqué), chaque carte `<Link href="/metiers/{slug}">` vers la fiche détail existante (Story 3.12, inchangée). `/metiers` est déjà dans `ROUTE_ALLOWED_ROLES` (`["student", "parent"]`) — pas de nouvelle entrée nécessaire.
  - `apps/web/src/app/(authenticated)/accueil/page.tsx`'s `MetiersModule` — quand `professions.length === 0`, ajoute un bouton "Voir la liste des métiers" → `/metiers`, à côté du texte existant (ne le remplace pas).
  - **Pas de nouvel item de nav** — `/metiers` reste accessible via ce bouton contextuel et l'URL directe ; ajouter un item de nav dédié serait un choix produit distinct (le catalogue n'est qu'un repli, pas une section de premier plan), hors scope ici.

## 3. Acceptance Criteria

**AC1** — `GET /api/v1/professions/` (authentifié, rôle `student`) retourne les métiers actifs, paginés, triés par nom.
**AC2** — Sur `/accueil`, si `professions.length === 0` dans "Tes métiers", un bouton "Voir la liste des métiers" apparaît et route vers `/metiers`.
**AC3** — `/metiers` affiche une grille de toutes les fiches (nom + secteur + salaire médian si connu), chaque carte cliquable vers `/metiers/{slug}` (fiche détail inchangée).
**AC4** — Rôle non autorisé (`counselor`, `school_admin`, etc.) → guard existant (`ROUTE_ALLOWED_ROLES["/metiers"]`) refuse déjà l'accès, aucun changement nécessaire.

## 4. Out of scope (explicite)

- **Scraping / extension du référentiel au-delà des 52 métiers seedés** — story dédiée future, mentionnée explicitement par l'utilisateur.
- **Liste des établissements** (`/schools` a le même trou — seul `/schools/[slug]` existe) — reporté "à un autre moment" par l'utilisateur. Noté dans `deferred-work.md` pour ne pas se perdre, pas construit ici.
- **Filtres/recherche dans le catalogue** — non demandé, ajoutable dans une itération suivante si le besoin apparaît.
- Nouvel item de nav pour `/metiers` — décision produit distincte, non demandée.

## 5. Review Findings

**Bug pré-existant trouvé et corrigé en cours de route** : `apps/professions/tests/test_endpoints.py` est marqué `postgresql_only` (17 tests) mais ses fixtures `student_user`/`admin_user` n'étaient pas wrappées en `bypass_rls()` — chaque test du fichier échouait dès le setup sur un vrai rôle Postgres NOSUPERUSER (`new row violates row-level security policy for table "users"`), sans rapport avec cette story mais découvert en essayant de vérifier les nouveaux tests contre Postgres. Corrigé (même pattern que les fixes RLS des sessions précédentes) — 22/22 tests passent maintenant sur Postgres réel.

**Vérification** :
- Backend : `PublicProfessionListView` — 5 nouveaux tests (200 pour student, exclut les champs lourds, exclut les inactifs, 401 anonyme, 403 admin) + les 17 pré-existants, tous verts sur Postgres réel (`--ds=path_advisor.settings.test_postgres`). `assert_rbac_declared.py` : 242 endpoints OK. `ruff check` clean.
- Frontend : 17 tests (catalogue page, bouton repli sur `/accueil`, `fetchProfessions`). `tsc --noEmit`/`eslint` clean sur les fichiers touchés. 759 passed / 12 échecs pré-existants sans rapport (mêmes qu'avant cette story).
- Smoke test Docker : `seed_professions` exécuté en local (52 métiers actifs, dépasse les "30 d'exemple" demandés) ; `/metiers` → 200, affiche les 52 cartes ; `/accueil` → 200.
- **Non vérifiable en live** : le bouton "Voir la liste des métiers" sur `/accueil` ne s'affiche que si `professions.length === 0` — dans cet environnement, le service IA renvoie toujours au moins une recommandation à faible confiance même pour un profil totalement vide (testé avec un compte neuf dédié), donc cette branche ne se déclenche jamais en pratique ici. Couvert et confirmé fonctionnel par le test unitaire dédié (`page.test.tsx`, reco mockée à `[]`).

**Reporté explicitement par l'utilisateur** (noté dans `deferred-work.md`) : liste/catalogue des établissements (**traité depuis**, voir Story 4.14) ; scraping/extension du référentiel au-delà des 52 métiers seedés.

## 6. Post-review follow-up (2026-09-05) — icône par secteur

Demande explicite : "tu saurais rajouter une image à côté de chaque métier ?" Le modèle `Profession` n'a aucun champ image (le scraping/enrichissement du référentiel reste une story future distincte, cf. §4). En attendant de vraies photos, chaque carte du catalogue affiche désormais un badge coloré avec une icône `lucide-react` par secteur (13 secteurs mappés + repli neutre) plutôt qu'un bloc de texte nu — pas d'asset externe, aucun risque d'image cassée. Voir `apps/web/src/app/(authenticated)/metiers/page.tsx` (`SECTOR_VISUALS`) et Story 8.8 §11 pour le contexte plus large des itérations `/accueil` de la même session.

Test ajouté : `metiers/page.test.tsx` — un badge par carte, y compris repli pour un secteur inconnu. Vérifié : 761 passed (12 pré-existants sans rapport), tsc/eslint clean, smoke test Docker (52 badges rendus).
