# Story 6.7 : Consentement élève → conseillère pour vue profil individuel

**Status:** done

## 1. User Story

As a système Path-Advisor,
I want exiger un consentement explicite de l'élève avant qu'une conseillère puisse voir son profil individuel détaillé,
So that la confidentialité élève soit respectée conformément à FR44.

## 2. Scope decisions

- **Infra déjà pré-plombée.** L'aggregateur/registre `apps.profiles.access_list` (Story 1.9/1.10) référençait déjà littéralement `"counselor_consent"` comme nom de source (dans `visibility_matrix.py` et `revoker.py`'s `_SOURCE_TO_TIER_TYPE`) et les tests génériques attendaient déjà ce nom exact. Cette story construit précisément ce qui était anticipé : le modèle `CounselorConsent` + l'adaptateur `CounselorConsentSource`.
- **Pas de token/lien anonyme** (contrairement à `ParentalConsent`, Story 1.4) : l'élève est déjà authentifié (compte élève B2B existant via CSV import, Story 6.5), donc la décision se prend directement dans son espace — pas besoin d'un flow d'invitation par email à un tiers non-inscrit.
- **Une seule ligne par (élève, conseillère)** — une nouvelle demande après refus réutilise la même ligne (`status` repasse à `pending`) plutôt que d'accumuler un historique de lignes distinctes.
- **Pas de `TenantScopedModel`/RLS** pour `CounselorConsent` : comme `ParentStudentLink` (Story 6.1) et `EarlyOutreachRequest` (Story 5.4), l'autorisation tient entièrement dans les FK `student`/`counselor` — pas de données partagées/agrégées à protéger par RLS en plus.
- **Autorisation réelle du côté conseillère** = appartenance au même établissement (`counselor.tenant_id == invitation.cohort.establishment_id`), vérifiée explicitement dans la vue — sans ça, une conseillère aurait pu demander le consentement de n'importe quel élève de n'importe quel établissement (faille de sécurité comblée au passage, pas seulement l'AC littérale).
- **Bug RLS réel détecté et corrigé** (3ème fois cette session, même classe de bug que 5.6/5.7/5.9) : `student_import_invitations` a `FORCE ROW LEVEL SECURITY` (migration 0003) — une session conseillère ne peut pas lire la ligne `users` de l'élève ni l'invitation d'un autre tenant sans `bypass_rls` après l'autorisation métier. Détecté uniquement au passage Postgres, invisible sur SQLite.

## 3. Acceptance Criteria

**AC1 — Blocage sans consentement**
**Given** un élève appartient à la cohorte d'un établissement pilote
**When** la conseillère tente d'accéder au profil individuel
**Then** si pas de consentement → accès bloqué (vue restreinte)
**And** une option "Demander le consentement" est proposée
→ `require_granted_consent` (le gate que la Story 6.8 appelle) implémenté ; la vue restreinte elle-même est la Story 6.8.

**AC2 — Demande**
**Given** la conseillère demande le consentement
**When** la demande est envoyée
**Then** l'élève reçoit une notification
**And** il voit un `ConsentDialog` expliquant ce que la conseillère verra/ne verra pas
→ Implémenté : email + `<PendingCounselorConsents>` (nouveau, sur `/parametres/confidentialite/acces-tiers`) affichant le `<ConsentDialog>` générique (Story 1.14) réutilisé tel quel.

**AC3 — Acceptation**
**Given** l'élève accepte
**When** le consentement est enregistré
**Then** la conseillère peut consulter le profil
**And** l'accès est loggué et révocable à tout moment
→ Implémenté : `decide_consent` (audit `establishments.counselor_consent_decided`) ; révocation déjà câblée via `CounselorConsentSource.revoke` (le même endpoint générique `POST /profile/access-list/{id}/revoke/` de la Story 1.10, zéro nouveau code de révocation à écrire).

**AC4 — Refus**
**Given** l'élève refuse
**When** le refus est enregistré
**Then** la conseillère ne peut pas accéder
**And** elle peut redemander une fois plus tard (cooldown 7 jours)
→ Implémenté : `cooldown_active` property + `ConsentCooldownActive` (429).

## 4. Out of scope (deferred)

- La vue restreinte "nom + cohorte + flag consentement requis" (Story 6.8).
- Le profil individuel complet (Story 6.8).
- Notification de révocation à la conseillère par email (le pattern parental l'a via une tâche Celery dédiée ; ajoutée seulement si un besoin réel se confirme — l'audit trail suffit pour l'instant).

## 5. Review Findings

**Backend :**
- `CounselorConsent` (nouveau modèle, migration `0005`), `CounselorConsentStatus`, `cooldown_active` property.
- 3 nouvelles exceptions (`ConsentCooldownActive` 429, `ConsentNotGranted` 403, `ConsentAlreadyDecided` 409) + `StudentNotInCounselorsEstablishment` (403, faille comblée).
- `apps/establishments/services/counselor_consent.py` (nouveau) : `request_consent`, `list_pending_consent_requests`, `decide_consent`, `require_granted_consent`, `touch_last_accessed` (prêt pour la Story 6.11).
- `apps/profiles/access_list/sources/counselor_consent.py` (nouveau) : plug direct dans l'infra Story 1.9/1.10 existante — liste + révocation + `display_name_for`.
- 3 nouveaux endpoints (`counselor-consent-request`, `student-pending-consents`, `student-decide-consent`), nouveau montage `api/v1/establishments/` (`cohort_urls.py`, distinct de l'admin `api/v1/admin/`).
- **Vérifié :** 12/12 tests dédiés (SQLite + Postgres réel — le bug RLS ci-dessus détecté puis corrigé lors du passage Postgres), suite complète 1370 passed (0 régression), ruff/`assert_rbac_declared`(280)/`manage.py check`/migrations clean. Les 27 échecs Postgres pré-existants dans `apps/profiles/tests/test_revoke_endpoint.py`/`test_access_list_endpoint.py` sont confirmés non liés à cette story (reproduits à l'identique sur `main` avant tout changement, via `git stash`).

**Frontend :**
- `lib/api/counselor-consent.ts` (nouveau), `COUNSELOR_CONSENT_REQUEST_COPY` (nouveau dict i18n).
- `<PendingCounselorConsents>` (nouveau), intégré sur `/parametres/confidentialite/acces-tiers` — réutilise `<ConsentDialog>` (Story 1.14) sans aucune modification du composant générique.
- **Vérifié :** 4 nouveaux tests, suite complète 844 passed (12 échecs pré-existants non liés, même chiffre que toutes les stories précédentes), tsc/eslint clean.

**Smoke test Docker (réel, end-to-end) :** demande créée (email reçu, vérifié via Mailpit) → élève liste sa demande pending → accepte → `require_granted_consent` (le gate de la Story 6.8) confirme l'accès → la demande apparaît dans la liste d'accès unifiée (`tier_type=counselor`) → `touch_last_accessed` stampe correctement (prêt pour la Story 6.11). Données de test nettoyées après vérification.
