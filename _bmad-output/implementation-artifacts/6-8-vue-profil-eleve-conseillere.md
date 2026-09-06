# Story 6.8 : Vue profil individuel élève côté conseillère

**Status:** done

## 1. User Story

As a conseillère d'orientation,
I want consulter le profil individuel détaillé d'un élève ayant donné son consentement,
So that je puisse préparer un entretien d'orientation personnalisé.

## 2. Scope decisions

- **Gate = `require_granted_consent` (Story 6.7)**. Chaque fonction de `counselor_profile.py` appelle ce gate en premier — `ConsentNotGranted` (403, handler RFC7807 global) propage avant que quoi que ce soit dans ce module ne s'exécute. La page frontend rend un fallback "Consentement requis" plutôt qu'une page d'erreur générique.
- **Réutilisation de `apps.family.services.parent_view`** (`get_child_professions`, `get_child_mes_paris`) plutôt que dupliquer la logique de recommandation IA/favoris — aucune des deux fonctions ne fait d'autorisation parent-spécifique en interne (ça vit dans `resolve_linked_child`, jamais appelé ici) : réutilisation sûre, pas une violation de couches.
- **"Vœux en construction" omis** — aucun modèle de données de ce type n'existe dans le codebase (pas de modèle de vœux Parcoursup) ; différé plutôt que simulé, même logique que le champ conversion-Parcoursup de la Story 5.10.
- **Export PDF via `reportlab` bas niveau** (`canvas.Canvas`, nouvelle dépendance `reportlab==5.0.1`), pas un moteur de rapports générique — un document texte d'une page (synthèse profil + notes), proportionné au besoin réel.
- **Notes = propriété exclusive de la conseillère auteure** — aucun chemin de lecture côté élève ni côté autre conseillère (`CounselorNote.objects.filter(counselor=counselor, student_id=student_id)` scope systématique).
- **Pas de credentials/paiement exposés** (NFR-S4) — le dict de profil n'assemble jamais une sérialisation brute de `User`/`Subscription`, seulement les champs listés dans l'AC.
- **Frontend** : nouvelle route `/cohorte/eleves/[studentId]` (le préfixe `/cohorte` est déjà déclaré dans `ROUTE_ALLOWED_ROLES` pour `counselor`/`path_admin` depuis une story antérieure, mais aucune page n'existait encore sous ce chemin) — panneau de notes en Client Component (`<CounselorNotesPanel>`), reste du profil en Server Component.

## 3. Acceptance Criteria

**AC1 — Vue profil**
**Given** une conseillère a un consentement `granted` non révoqué pour un élève
**When** elle consulte `GET /students/{id}/profile/`
**Then** elle voit : cohorte, top 8 métiers recos, mes paris, activité récente (dernière connexion)
**And** sans consentement → 403 (`ConsentNotGranted`)
✅ `get_student_profile_for_counselor`, `counselor_student_profile` view, page `/cohorte/eleves/[studentId]`.

**AC2 — Notes privées + export**
**Given** une conseillère consultant un profil consenti
**When** elle ajoute une note ou exporte la fiche entretien
**Then** la note est visible uniquement par elle (jamais par l'élève ni une autre conseillère)
**And** le PDF contient la synthèse profil + ses notes personnelles
✅ `add_counselor_note`/`list_counselor_notes`, `export_interview_sheet_pdf`, `<CounselorNotesPanel>`, bouton "Exporter fiche entretien (PDF)".

**AC3 — Traçabilité**
**Given** une conseillère consulte un profil
**Then** un audit log `establishments.counselor_profile_viewed` est créé et `last_accessed_at` est mis à jour sur le consentement (seam Story 6.11)
✅ vérifié par test + smoke test Docker (2 vues → `AUDIT_COUNT=2`, `last_accessed_at` non nul).

## 4. Fichiers modifiés/créés

**Backend**
- `apps/establishments/models.py` — `CounselorNote` model.
- `apps/establishments/migrations/0006_counselornote.py`
- `apps/establishments/services/counselor_profile.py` (new) — `get_student_profile_for_counselor`, `add_counselor_note`, `list_counselor_notes`, `export_interview_sheet_pdf`.
- `apps/establishments/serializers.py` — `CounselorProfileProfessionSerializer`, `CounselorProfileEcoleSerializer`, `CounselorStudentProfileSerializer`, `CounselorNoteSerializer`, `CounselorNoteCreateSerializer`.
- `apps/establishments/counselor_views.py` — `counselor_student_profile`, `counselor_student_notes`, `counselor_interview_sheet_pdf`.
- `apps/establishments/cohort_urls.py` — 3 nouvelles routes sous `students/<student_id>/{profile,notes,interview-sheet.pdf}/`.
- `apps/establishments/tests/test_counselor_profile.py` (new, 8 tests).
- `pyproject.toml`/`uv.lock` — `reportlab==5.0.1` ajouté.

**Frontend**
- `lib/api/counselor-profile.ts` (new) — client API + `buildInterviewSheetPdfUrl`.
- `components/features/establishments/counselor-notes-panel.tsx` (new) + test (4 tests).
- `app/(authenticated)/cohorte/eleves/[studentId]/page.tsx` (new) + test (3 tests).

## 5. Vérifications

- Ruff : `0` erreur sur `apps/establishments` (2 corrigées : `I001` import order, `RUF059` variable inutilisée).
- Tests SQLite : `8 passed` (`test_counselor_profile.py`).
- Tests Postgres (parité RLS) : `20 passed` (`test_counselor_profile.py` + `test_counselor_consent.py`) — aucun bug RLS cette fois (contrairement aux Stories 5.6/5.7/6.7).
- `manage.py check` : 0 issue.
- `makemigrations --check --dry-run` : uniquement la dérive pré-existante connue sur `bulletins` (non liée).
- `assert_rbac_declared.py` : 283 endpoints passent la gate RBAC.
- Suite backend complète : `1378 passed, 144 skipped`, 0 régression.
- Frontend : nouveaux tests (7) passent ; suite complète `851 passed, 12 failed` (échecs pré-existants non liés, onboarding step-3 + parcours) ; `eslint` 0 erreur sur les nouveaux fichiers ; `tsc --noEmit` 0 nouvelle erreur (uniquement les erreurs pré-existantes déjà documentées).
- Smoke test Docker live : profil (top-8 métiers via appel réel à l'ai-service, mes paris, activité récente), ajout + liste de note, export PDF (`%PDF-1.3`, 1912 octets), audit log (`AUDIT_COUNT=2`), `last_accessed_at` stampé — données de test nettoyées après vérification.
