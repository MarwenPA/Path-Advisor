# Story 9.2 — CRUD référentiel formations / écoles (+ calendrier Parcoursup)

Statut : review · Epic 9 · 2026-09-26

## 1. User Story

As a admin Path-Advisor, I want créer, modifier et supprimer des fiches écoles/formations, So that le référentiel 100+ formations reste de qualité (FR48).

ACs : filtres type/région/statut ; création avec champs + formations associées ; **import CSV** (open data Parcoursup) avec validation par ligne + conflits + drill-down manuel ; traçabilité (NFR-S4) + recalcul des stats d'admission ; **[amendement epic]** CRUD des jalons Parcoursup (délégué 8.3), jalon notifié = date verrouillée.

## 2. Décisions de périmètre

1. **Miroir exact du patron 9.1** : `School.status` (sync `is_active` dans `save()`, backfill), `SchoolRevision` (snapshot par écriture, rollback append-only), service unique avec `record_audit` transactionnel, « supprimer » = archiver (une école est référencée par Parcours, favoris, stats, envois anticipés — et 7.10 a déjà toute l'UX « établissement désactivé » côté élève).
2. **API** : l'`AdminSchoolViewSet` read-only (4.x) devient un `ModelViewSet` (create/partial_update via le service) + actions `archive`/`revisions`/`rollback` + filtres `type`/`region`/`status`/`q`. Le router existant absorbe tout — pas de nouvelle URL manuelle. `AdminFormationViewSet` : passe en CRUD complet aussi (une formation est un sous-objet simple de l'école, révisions portées par l'école ? Non : les formations n'ont pas d'historique propre — hors AC, la traçabilité demandée porte sur l'école ; consigné).
3. **Import CSV** : `POST /admin/schools/import-csv/` (multipart, `IsPathAdmin`). Délimiteur `;`, en-têtes attendues documentées (sous-ensemble utile de l'open data Parcoursup : `slug;name;type;city;region;postal_code;public_private;selectivity_index;official_url;description`). Chaque ligne validée par le serializer d'écriture ; **conflit = slug existant** → la ligne n'écrase RIEN, elle sort dans `conflicts[]` avec l'existant et l'entrant côte à côte ; le drill-down = l'UI ouvre la fiche existante, la résolution est un PATCH manuel (l'AC demande la résolution manuelle, pas un merge automatique). Import créé sous une seule transaction pour les `created` (tout-ou-rien) ; chaque création passe par le service (révision `created` + audit + statut `draft` par défaut — un import de masse ne publie jamais directement, garde éditoriale).
4. **« Job de recalcul des stats d'admission » : lazy par construction, consigné.** La stat personnalisée est ré-upsertée à CHAQUE consultation de la fiche par l'élève (`schools/views.py:270`) et la baseline population au même endroit — une école modifiée est reflétée au prochain passage. Exception connue et assumée : les stats GELÉES post-réponse-outreach (5.8) ne sont pas recalculées (le gel est voulu — la réponse de l'école domine l'estimation) ; consigné.
5. **Jalons Parcoursup (amendement 8.3)** : API `IsPathAdmin` liste/création/édition sur `ParcoursupMilestone` + règle serveur « `notified_at` posé ⇒ `date` et `notify_days_before` verrouillés » (l'email est parti, changer la date mentirait sur l'historique ; le kind/campagne restent immuables par construction — contrainte unique). Pas de suppression (l'exactly-once 8.3 repose sur la ligne). UI `/admin/calendrier` groupée par campagne.
6. **Front** : `/admin/ecoles` (table + filtres + bloc import CSV avec rapport created/conflicts/errors et liens drill-down), `/admin/ecoles/[slug]` (fiche + historique + rollback), `/admin/calendrier`. Mêmes composants/conventions que 9.1.

## 3. Périmètre technique

- Migrations schools : `status` + `SchoolRevision` + backfill. Service `apps/schools/services/referential_admin.py`. Tests miroir de 9.1 + import CSV (créées/conflits/erreurs, tout-ou-rien, draft par défaut) + jalons (verrouillage post-notification).
- RBAC : endpoints admin → aucun AllowAny nouveau.

## 4. Résultats (implémentation)

**Livré.**

- **Miroir 9.1 sur School** : `status` + sync `is_active` (migrations 0008/0009), `SchoolRevision` (+action `imported`), service `referential_admin.py` (révision + audit transactionnels, archive = suppression) ; 4 writers legacy `is_active=False` migrés (2 attrapés par la lane RLS locale — leçon 9.1 appliquée AVANT la CI cette fois).
- **API** : `AdminSchoolViewSet` read-only (4.x) → `ModelViewSet` complet, lookup par slug, filtres `q/type/region/status`, actions `archive`/`revisions`/`rollback` + `import-csv` (multipart 2 Mo max, UTF-8).
- **Import CSV (AC2)** : validation par ligne via le serializer d'écriture ; conflits (slug existant) JAMAIS écrasés — rapport existant/entrant côte à côte, résolution = PATCH manuel depuis la fiche (drill-down) ; créations en **brouillon** (un import de masse ne publie jamais directement) sous une transaction tout-ou-rien ; doublons intra-fichier et colonnes manquantes signalés ; audit `referential.schools_csv_imported`.
- **Jalons Parcoursup (amendement 8.3)** : GET/POST/PATCH `IsPathAdmin`, doublon (kind,campagne) → 400, **jalon notifié → date/fenêtre verrouillées (409)** avec message explicite ; pas de DELETE (l'exactly-once 8.3 vit sur la ligne) ; audit par écriture.
- **« Recalcul des stats » : lazy par construction, consigné (§2.4)** — la stat est ré-upsertée à chaque consultation de fiche ; exception assumée : stats gelées post-outreach (5.8).
- **Front** : `/admin/ecoles` (table filtres + bloc import avec rapport et liens d'arbitrage), fiche école (édition scalaires + statut + historique/rollback), `/admin/calendrier` (groupé par campagne, création, date éditable seulement si non notifié, badge « Notifié — date verrouillée »).
- **Tests** : 8 backend (`test_admin_crud.py` schools — cycle complet, draft invisible public, filtres, CSV drafts/conflits/erreurs/colonnes manquantes, jalon doublon+lock 409) + 4 front (filtre piloté, rapport CSV avec drill-down, jalon verrouillé vs éditable, création jalon). Fast lane **1568**, lane RLS locale **155**, web **1015**, mypy = baseline (28 préexistants), RBAC 311.
- **Preuve live** (session MFA réelle) : école draft **201** → import CSV multipart : `created: [bts-oceano-92]`, `conflicts: [lycee-maritime-92]` (fiche intouchée) → jalon **201** → PATCH non-notifié **200** → `notified_at` posé → PATCH date **409** « déjà été notifié aux élèves ».
