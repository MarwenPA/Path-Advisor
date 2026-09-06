# Story 6.11 : Composant `PermissionList` étendu (révocation 1-tap + audit visible)

**Status:** done

## 1. User Story

As a élève,
I want un composant `PermissionList` enrichi qui montre tous mes accès tiers + dernière consultation + révocation 1-tap,
So that je garde un contrôle transparent et instantané sur qui voit mon profil (FR8 + FR9 + UX-DR16).

## 2. Scope decisions

- **`TierAccessCard` (Story 1.9) est le composant `PermissionList`** — cette story l'étend plutôt que d'en créer un second (même nom d'AC, même page `/parametres/confidentialite/acces-tiers`). La révocation 1-tap existe déjà (`RevokeAccessButton`, Story 1.10) — non retouchée.
- **"Date dernière consultation" — pas de nouvelle table de tracking.** Ajout du champ `last_accessed_at` au DTO `AccessListEntry` : pour `CounselorConsentSource`, lu directement depuis `CounselorConsent.last_accessed_at` (déjà stampé par `touch_last_accessed`, Story 6.7/6.8 — la colonne existait déjà "en avance" pour cette story précisément). Pour `ParentalConsentSource`, reste `None` — aucun tracking équivalent n'existe sur `ParentalConsent` ; documenté, pas fabriqué.
- **Historique d'accès (90 jours) — réutilise `AuditLog` existant**, pas de nouveau modèle. `parent.child_dashboard_viewed` et `establishments.counselor_profile_viewed` (déjà écrits par les services de vue profil) sont filtrés par `(actor_id=<viewer résolu>, subject_id=<élève>, created_at >= now-90j)`. Pour un consentement parental créé avant que le parent n'ait un compte Path-Advisor (`parent_user_id IS NULL`, ADR-0003), l'historique est légitimement vide (aucun `actor_id` à matcher) — pas un bug.
- **Export CSV** — même pattern `<a href>` que les Stories 5.10/6.9 (pas de fetch/blob).
- **Modale sans librairie de dialog** — aucune librairie headless-ui/radix installée sur cette surface ; `role="dialog"` + `aria-modal` maison, cohérent avec le reste de l'app.

## 3. Acceptance Criteria

**AC1 — Nom + rôle + date d'octroi + dernière consultation + révoquer 1-tap**
✅ `TierAccessCard` étendu : ligne "Dernière consultation" ajoutée (relative + `<time>` absolu), bouton "Révoquer" déjà présent depuis la Story 1.10.

**AC2 — Historique d'accès (90 jours) + export CSV**
**Given** je tape sur "Voir l'historique d'accès"
**When** la modale s'ouvre
**Then** je vois la liste horodatée des consultations sur 90 jours + export CSV
✅ `<ViewAccessHistoryButton>` + `<AccessHistoryModal>`, `GET .../history/`, `GET .../history.csv/`.

**AC3 — Révocation 1-tap**
✅ Déjà livré par la Story 1.10 (`ConsentDialog` + `RevokeAccessButton`) — non retouché.

## 4. Fichiers modifiés/créés

**Backend**
- `apps/profiles/access_list/dto.py` — `AccessListEntry.last_accessed_at`.
- `apps/profiles/access_list/sources/counselor_consent.py` — populate `last_accessed_at`.
- `apps/profiles/access_list/history.py` (new) — `get_access_history`, `export_access_history_csv`.
- `apps/profiles/serializers.py` — `last_accessed_at` sur `AccessListEntrySerializer`.
- `apps/profiles/views/access_list.py` — `access_list_entry_history`, `access_list_entry_history_export`.
- `apps/profiles/urls.py` — 2 nouvelles routes `history/` et `history.csv/`.
- `apps/profiles/tests/test_access_list_history.py` (new, 6 tests).

**Frontend**
- `lib/api/access-list.ts` — `last_accessed_at`, `fetchAccessHistory`, `buildAccessHistoryExportUrl`.
- `lib/i18n/fr/access-list.ts` — copie historique.
- `components/features/privacy/access-history-modal.tsx` (new) + test (4 tests).
- `components/features/privacy/view-access-history-button.tsx` (new) + test (1 test).
- `components/features/privacy/tier-access-card.tsx` — ligne "Dernière consultation" + bouton historique ; tests étendus (+3).

## 5. Vérifications

- Ruff : 0 erreur.
- Tests SQLite : `6 passed` (`test_access_list_history.py`).
- Tests Postgres : les 6 tests échouent sur `force_login`/`update_last_login` — **confirmé pré-existant et non lié** : `test_access_list_endpoint.py` (fichier existant, non touché par cette story) échoue de façon identique (10/11 tests) sur le même `DatabaseError: Save with update_fields did not affect any rows.` — bug d'infra de test Postgres déjà documenté cette session (27 échecs pré-existants trouvés lors de la Story 6.7), pas une régression de cette story.
- `manage.py check` : 0 issue. `assert_rbac_declared.py` : 287 endpoints (+2).
- Suite backend complète : `1393 passed, 144 skipped` (+6 vs Story 6.9), 0 régression.
- Frontend : 8 nouveaux tests passent ; suite complète `866 passed, 12 failed` (échecs pré-existants non liés), `eslint` 0 erreur, `tsc` 0 nouvelle erreur.
- Smoke test Docker live : consentement conseillère accordé → vue profil déclenchée → `last_accessed_at` non nul confirmé via `AccessListAggregator`, `get_access_history` retourne 1 consultation — données de test nettoyées après vérification.
