# Story 1.16 : Faire réellement tourner le lane de tests RLS (jamais exécuté)

**Status:** review

## 0. Résultat (2026-09-08)

Lane RLS complet (`-m "rls or postgresql_only"`, la sélection exacte de la CI) : **149 passants, 0 échec** — contre 149 erreurs au départ. Lane SQLite rapide inchangé : 1448 passants, 151 skippés. `ruff` propre, aucune nouvelle erreur mypy.

**Aucun trou de politique RLS trouvé.** Les 149 échecs étaient tous des défauts de harnais, et une fois l'arrange et la persistance des GUC corrigés, **chaque assertion d'isolation stricte passe sans avoir été modifiée** contre les politiques telles que migrées. C'est le résultat qu'on espérait sans pouvoir le présumer.

Trois découvertes au-delà du périmètre annoncé :

1. **Des tests d'isolation ne prouvaient rien.** `students/test_rls.py` posait ses GUC avec `set_config(..., is_local => true)` **hors** `transaction.atomic()`. Vérifié empiriquement : en autocommit, un GUC local est perdu dès l'instruction suivante. Sa phase *act* tournait donc sur une session anonyme, pas sur l'identité annoncée — `test_anonymous_session_sees_nothing` passait pour la mauvaise raison, et les autres testaient la branche « deny by default » au lieu de celle de leur nom.
2. **Des contrôles positifs manquaient.** `rowcount == 0` sur un UPDATE croisé est vacu : une session morte ne matche rien non plus. Chaque test d'isolation a désormais un contrôle prouvant que le même harnais, avec les GUC du propriétaire légitime, atteint bien la ligne.
3. **Trois bugs de requête jamais exécutés** dans le même fichier : une liste Python bindée en `ARRAY` Postgres vers une colonne `jsonb`, une colonne `NOT NULL` (`bulletins_status`, story 2.7) absente d'un `INSERT` brut — de sorte qu'une violation de contrainte pouvait se faire passer pour le rejet RLS attendu — et une comparaison de `jsonb` texte à une liste Python.

`_set_gucs` lève désormais une exception s'il est appelé hors `transaction.atomic()`, pour que cette classe de bug ne puisse pas revenir silencieusement.

## 1. Constat

**Le pipeline `ci-api` n'a jamais été vert : 100 échecs sur 100 runs** (`gh run list --workflow=ci-api --limit 100` → `{"failure": 100}`). Le job fautif est `rls-tests` ; l'autre job du même workflow (`lint-test-openapi`) passe.

Conséquence directe : **les tests d'isolation multi-tenant n'ont jamais été exécutés en intégration continue.** Ce sont ceux qui vérifient qu'un élève ne peut pas lire le profil d'un autre, qu'une conseillère ne voit pas une cohorte d'un autre établissement, et que `bypass_rls()` est bien la seule porte de sortie — sur une application manipulant des données de mineurs (RGPD, HDS, ISO 27001, BSI C5).

C'est le livrable T7 de la Story 1.8 qui n'a jamais abouti, sans que rien ne le signale.

## 2. Causes, diagnostiquées et vérifiées en local

Reproduites sur un conteneur jetable répliquant exactement le service CI. Trois couches empilées, **les trois premières déjà corrigées** dans la PR de correctifs de review :

1. **`CREATEDB` manquant.** Le rôle `path_advisor_test` est créé `NOSUPERUSER NOBYPASSRLS` — indispensable pour que `FORCE ROW LEVEL SECURITY` s'applique réellement — mais sans `CREATEDB`, donc le test runner Django ne peut pas créer `test_path_advisor_test`. → `permission denied to create database`, 149 erreurs.
2. **Image Postgres sans pgvector.** `image: postgres:16` alors que `core.0001_init_extensions` exige l'extension `vector`. Défaut identique à celui corrigé dans `ci-lighthouse.yml` quelques lignes plus loin. → `extension "vector" is not available`.
3. **`CREATE EXTENSION` exige un superutilisateur**, ce que le rôle ne peut pas être par conception. Contourné en installant l'extension dans `template1` : toute base créée ensuite (dont celle de Django) en hérite, et le `IF NOT EXISTS` de la migration devient un no-op.

Après ces trois correctifs, la suite **s'exécute enfin** : de 149 erreurs à **76 tests passants**, 26 échecs, 47 erreurs.

## 3. Ce qui reste à faire — l'objet de cette story

Les 73 échecs/erreurs restants portent tous le même message :

```
new row violates row-level security policy for table "users"
```

Autrement dit : la RLS est désormais réellement appliquée (c'est le but de ce lane), et **les fixtures de test n'ont jamais été adaptées à ce régime** — elles insèrent des utilisateurs sans passer par le helper `bypass_rls()` qui existe pourtant (`apps/api/apps/core/rls.py`).

⚠️ **Point important à ne pas escamoter** : tant que ce harnais ne tourne pas au vert, **personne ne sait si les politiques RLS elles-mêmes sont correctes.** Il peut ne s'agir que de plomberie de fixtures — ou le lane peut révéler de vraies failles d'isolation. Les deux hypothèses sont ouvertes et c'est précisément pourquoi cette story compte.

## 4. Acceptance Criteria

**AC1** — `uv run pytest -m "rls or postgresql_only" --ds=path_advisor.settings.test_postgres` passe intégralement en local contre un Postgres provisionné comme la CI (rôle `NOSUPERUSER NOBYPASSRLS CREATEDB`, extension `vector` dans `template1`).

**AC2** — Le job `rls-tests` de `ci-api` est **vert en CI réelle** (confirmé via `gh run watch`, pas déduit d'un run local).

**AC3** — ~~Les fixtures créant des utilisateurs/tenants passent explicitement par `bypass_rls(reason=...)`~~

> ⚠️ **AC3 telle qu'écrite initialement était fausse et contredisait le code.** `apps/core/rls.py` interdit explicitement ce que cette AC demandait : *« DO NOT call bypass_rls() from a generic helper. The set of call sites MUST stay countable on one hand »*. L'utiliser depuis des fixtures aurait fait exploser la surface de grep sur laquelle un relecteur s'appuie, et émis une ligne d'audit par test.
>
> **AC3 corrigée** — les fixtures passent par `as_path_admin()` (`apps/core/rls_testing.py`, module test-only), qui réutilise la branche `path_admin` que **toutes** les politiques du dépôt possèdent déjà. Aucune nouvelle surface de bypass n'est introduite, et `bypass_rls()` garde ses call sites dénombrables.

**AC4** — Si un test révèle une faille d'isolation réelle (et non un défaut de fixture), elle est traitée comme un défaut de sécurité : correctif de politique + test de régression, et non contournement de la fixture pour faire passer le test. **Ne jamais affaiblir un test d'isolation pour obtenir du vert.**

**AC5** — `rls-tests` est ajouté aux checks requis de la branch protection de `main` une fois vert.

## 5. Contexte utile

- Provisionnement CI : `.github/workflows/ci-api.yml`, job `rls-tests`.
- Settings du lane : `apps/api/path_advisor/settings/test_postgres.py` (hérite de `settings.test`).
- `apps/api/conftest.py` contient déjà `_assert_non_superuser_in_postgres_lane` et un fixture autouse émettant `RESET ALL` entre les tests — comprendre ce contrat avant de toucher aux fixtures.
- Helper : `apps/api/apps/core/rls.py` (`bypass_rls()`, et l'avertissement explicite de ne pas le généraliser).

## 6. Pourquoi ça a pu passer inaperçu si longtemps

Aucune protection de branche n'existait sur `main` : un pipeline rouge n'empêchait aucun merge, et les PR étaient fusionnées sans attendre le statut CI. Le même mécanisme a laissé passer 20+ échecs de `ci-web`. La branch protection est traitée à part, mais c'est la cause systémique commune.
