# Story 3.7 — Demander une revue humaine d'une recommandation

**Epic:** 3 — Recommandation Vocationnelle (Premier Aha)
**Status:** review
**Sprint:** 6 (Recommandation vocationnelle)
**Story Key:** `3-7-revue-humaine-recommandation`
**Estimation:** S (small) — mirrors Story 3.8 pattern exactly: form + backend endpoint + audit log. ~1 j focused work.

> Exercice du droit RGPD art. 22 à l'intervention humaine. L'élève peut contester une recommandation qui lui semble incorrecte ou inappropriée. La demande est enregistrée et apparaît dans la file admin (Epic 9). La reco contestée est marquée visuellement "en revue" dans la session courante. Pattern identique à Story 3.8 (`ProfessionReport`) — réutiliser exactement les mêmes abstractions.

---

## 1. User Story

**As** an élève (Sarah, Mehdi, Léa),
**I want** to request a human review of a recommendation that seems incorrect or inappropriate,
**So that** I can exercise my RGPD art. 22 right to human intervention and the system learns from errors (FR23).

**Business value :** sans ce mécanisme, une reco absurde ou choquante laisse l'élève sans recours — confiance détruite, churn. Avec ce mécanisme, on respecte RGPD art. 22 ET on collecte des signaux qualité pour améliorer le modèle.

---

## 2. Acceptance Criteria (BDD)

### AC1 — Point d'entrée sur la fiche métier

**Given** je suis sur une fiche métier (`/metiers/[slug]`, composant `FicheMetier`)
**And** cette fiche correspond à une reco que j'ai reçue (score visible dans la hero)
**When** je consulte la fiche
**Then** je vois un bouton tertiary discret "Cette reco me dérange — demander une revue" avec icône Lucide `AlertCircle` (taille `sm`, `color-text-subtle`)
**And** ce bouton est visible seulement si un score est présent (reco active) — pas affiché en consultation directe URL sans score
**And** ce bouton n'est pas affiché en `variant="print"`

### AC2 — Formulaire de demande de revue (bottom sheet mobile / dialog desktop)

**Given** je tape sur "Cette reco me dérange — demander une revue"
**When** le formulaire s'ouvre
**Then** sur mobile : bottom sheet (slide-up) avec handle de glissement
**And** sur desktop : dialog centré (shadcn `Dialog`)
**And** le formulaire contient :
- **Titre** : "Demander une revue humaine" (h2 dans le dialog)
- **Sous-titre** : nom de la profession pré-rempli en `text-body-muted`
- **Raison** (Select shadcn, obligatoire) : 3 options
  - "Ne me correspond pas du tout"
  - "Métier choquant ou inapproprié"
  - "Autre"
- **Commentaire** (Textarea, optionnel, max 500 chars) : placeholder "Explique pourquoi cette reco te semble incorrecte (optionnel)"
- **Bouton primary** "Envoyer la demande" + **bouton tertiary** "Annuler"

**And** le Select "Raison" est le seul champ obligatoire

### AC3 — Soumission et feedback

**Given** je sélectionne une raison et clique "Envoyer la demande"
**When** la soumission est envoyée
**Then** le formulaire se ferme
**And** un toast 4 s confirme : "Demande envoyée — on te répondra sous 7 jours ouvrés"
**And** le bouton sur la fiche passe en état `review_requested` (icône `AlertCircle` filled + label "Revue demandée", `color-text-muted`, non cliquable — un seul signalement par fiche par session)

**Given** une erreur réseau lors de la soumission
**When** la requête échoue
**Then** le formulaire reste ouvert
**And** un message d'erreur inline s'affiche sous le bouton primary : "Envoi échoué — réessaie dans quelques instants"
**And** le bouton primary revient à l'état normal (pas de double-submit)

### AC4 — Backend : endpoint POST

**Given** l'API Django est déployée
**When** un élève authentifié envoie `POST /api/v1/students/me/recommendation-reviews/`
**Then** le payload est validé :
  ```json
  {
    "profession_slug": "infirmier-ere",
    "reason": "ne_correspond_pas | choquant_inapproprie | autre",
    "comment": "string (max 500 chars) | null"
  }
  ```
**And** un enregistrement `RecommendationReview` est créé avec :
  - `id` UUID (préfixe `rev_…` via `python-ulid`)
  - `student_id` FK → `accounts.User`
  - `profession_id` FK → `professions.Profession` (lookup par slug)
  - `reason` (choices)
  - `comment` (nullable, max 500)
  - `status` : `"pending"` (valeur initiale)
  - `created_at`

**And** la réponse est `201 Created` avec `{ "id": "...", "status": "pending" }`

**And** un utilisateur non authentifié reçoit `401 Unauthorized`

**And** un élève ne peut pas envoyer plusieurs demandes pour la même profession (contrainte `unique_together` sur `[student, profession]`) — retourne `409 Conflict` avec message clair si doublon

### AC5 — Audit log

**Given** une demande de revue est créée
**When** l'événement est loggué (Story 1.13)
**Then** l'audit log contient : `event: "recommendation_review_requested"`, `{ profession_slug, reason, student_id, review_id }`

### AC6 — File d'attente admin (Epic 9 — interface différée)

**Given** une demande est en `status: "pending"`
**When** l'admin consulte sa file (Epic 9)
**Then** il voit les demandes en attente triées par `created_at DESC`

**Note** : L'interface admin de traitement est hors scope de cette story (Epic 9). Cette story crée uniquement l'endpoint de lecture admin minimaliste.

**Given** l'admin appelle `GET /api/v1/admin/recommendation-reviews/`
**When** la réponse arrive
**Then** il voit la liste paginée des demandes en `status: "pending"` (permission `IsPathAdmin`)

### AC7 — Email de confirmation (différé Epic 8)

> Hors scope Sprint 6 — l'infrastructure email transactionnelle est couverte par Story 8.1. Pour le MVP, le toast AC3 est la seule confirmation côté élève.

**Note dans le code :** laisser un `TODO(story-8-1): send confirmation email` commenté dans la vue Django.

### AC8 — Accessibilité

**Given** le formulaire de demande de revue est ouvert
**When** je le parcours au clavier
**Then** le focus est trapé dans le dialog/bottom-sheet
**And** `Escape` ferme le formulaire (sans soumettre)
**And** l'ordre de focus : titre → Select raison → Textarea → bouton Envoyer → bouton Annuler
**And** le Select a un `<label>` associé (`htmlFor`)
**And** le toast de confirmation est annoncé par `aria-live="polite"`

### AC9 — Tests

**Given** les tests tournent (Vitest + RTL + pytest)
**When** tous les tests passent
**Then** :
- **Frontend :**
  - Tap "Cette reco me dérange" → formulaire ouvert
  - Soumission sans raison → champ en erreur, pas de submit
  - Soumission avec raison → `POST /api/v1/students/me/recommendation-reviews/` appelé + toast affiché
  - Erreur réseau → message erreur inline, formulaire reste ouvert
  - `Escape` → formulaire fermé
  - Après soumission → bouton en état `review_requested`
  - `variant="print"` → bouton absent
  - Score absent → bouton absent
- **Backend :**
  - `POST` payload valide → 201 + `RecommendationReview` créé
  - `POST` sans `reason` → 400
  - `POST` sans auth → 401
  - `POST` `comment` > 500 chars → 400
  - `POST` doublon (même étudiant + même profession) → 409
  - `GET /api/v1/admin/recommendation-reviews/` → 403 pour élève, 200 pour admin
  - Audit log créé à chaque demande

---

## 3. Tasks / Subtasks

### T1 — Backend : modèle + endpoint

- [x] Modèle `RecommendationReview` dans `apps/api/apps/recommendations/models.py`
  - Champs : `id` (ULID prefixé `rev_`), `student` FK, `profession` FK, `reason` (ChoiceField), `comment` (nullable, max 500), `status` (ChoiceField : pending/resolved_correct/resolved_fixed), `created_at`
  - `unique_together = [("student", "profession")]`
- [x] Migration `0001_recommendation_review.py` dans `apps/api/apps/recommendations/migrations/`
- [x] Serializers `RecommendationReviewCreateSerializer`, `RecommendationReviewResponseSerializer`, `RecommendationReviewAdminSerializer`
- [x] Vue `RecommendationReviewCreateView` (`POST /api/v1/students/me/recommendation-reviews/`)
- [x] Vue `RecommendationReviewAdminListView` (`GET /api/v1/admin/recommendation-reviews/`)
- [x] Routes dans `apps/api/apps/recommendations/urls.py`
- [x] Audit log Story 1.13 : `recommendation_review_requested`
- [x] Tests pytest : `apps/api/apps/recommendations/tests/test_reviews.py`

### T2 — Frontend : composant `ReviewRequestButton` + formulaire

- [x] Créer `apps/web/src/components/professions/ReviewRequestButton.tsx`
  - Props : `{ professionSlug: string; professionName: string; hasScore: boolean }`
  - État local : `open: boolean`, `reviewRequested: boolean`
  - Non rendu si `!hasScore`
- [x] Sous-composant `ReviewRequestForm.tsx` (formulaire interne, utilisé dans Dialog / Sheet)
- [x] Hook `useRequestRecommendationReview` dans `apps/web/src/hooks/` — TanStack Query mutation
- [x] Intégrer dans `FicheMetier.tsx` en pied de fiche (à côté du `ReportErrorButton`)

### T3 — Tests

**Backend (pytest) :**
- [x] POST valide → 201 + audit log
- [x] POST sans `reason` → 400
- [x] POST sans auth → 401
- [x] POST `comment` > 500 chars → 400
- [x] POST doublon → 409
- [x] GET admin list → 200 pour admin, 403 pour élève

**Frontend (Vitest + RTL) :**
- [x] Tous les cas AC9 frontend

---

## 4. Dev Notes

### 4.1 Wireframe ASCII — formulaire mobile (bottom sheet)

```
+-------------------------------------------+
|              --- (handle)                 |
|  Demander une revue humaine               | <- h2
|  Infirmier·ère de bloc opératoire         | <- text-body-muted
|                                           |
|  Raison *                                 |
|  +-------------------------------------+  |
|  |  Ne me correspond pas du tout     v |  | <- Select shadcn
|  +-------------------------------------+  |
|                                           |
|  Commentaire (optionnel)                  |
|  +-------------------------------------+  |
|  |  Explique pourquoi cette reco...   |  | <- Textarea 3 lignes
|  |                                     |  |
|  +-------------------------------------+  |
|                                  0/500    |
|                                           |
|  +-------------------------------------+  |
|  |   Envoyer la demande                |  | <- primary
|  +-------------------------------------+  |
|         Annuler                           | <- tertiary
+-------------------------------------------+
```

### 4.2 États du bouton

| État | Label | Icône | Couleur | Cliquable |
|---|---|---|---|---|
| Default | "Cette reco me dérange — demander une revue" | `AlertCircle` outline | `color-text-subtle` | Oui |
| Loading | "Envoi..." | spinner | `color-text-subtle` | Non |
| Requested | "Revue demandée" | `AlertCircle` filled | `color-text-muted` | Non |

### 4.3 Pattern à suivre — Story 3.8 est le modèle exact

**COPIER le pattern de 3.8, ne pas réinventer.** Les différences sont :
- App Django : `recommendations` au lieu de `professions`
- Endpoint : `/api/v1/students/me/recommendation-reviews/` (sous le namespace "students" car c'est une action sur la reco de l'élève)
- Champ obligatoire : `reason` (3 choix) au lieu de `error_type` (4 choix)
- Pas de champ `location` (pas pertinent pour une reco)
- Icône : `AlertCircle` au lieu de `Flag`
- Toast : "Demande envoyée — on te répondra sous 7 jours ouvrés"
- Bouton conditionnel : affiché seulement si `hasScore` (prop)

### 4.4 Modèle Django — squelette

```python
# apps/api/apps/recommendations/models.py
import uuid
from django.db import models
from python_ulid import ULID

class RecommendationReview(models.Model):
    class Reason(models.TextChoices):
        NE_CORRESPOND_PAS = "ne_correspond_pas", "Ne me correspond pas du tout"
        CHOQUANT = "choquant_inapproprie", "Métier choquant ou inapproprié"
        AUTRE = "autre", "Autre"

    class Status(models.TextChoices):
        PENDING = "pending", "En attente"
        RESOLVED_CORRECT = "resolved_correct", "Reco correcte — expliqué"
        RESOLVED_FIXED = "resolved_fixed", "Modèle ajusté"

    id = models.CharField(
        primary_key=True,
        max_length=32,
        default=lambda: f"rev_{ULID()}",
        editable=False,
    )
    student = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="recommendation_reviews",
    )
    profession = models.ForeignKey(
        "professions.Profession",
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    reason = models.CharField(max_length=30, choices=Reason.choices)
    comment = models.TextField(null=True, blank=True, max_length=500)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = [("student", "profession")]
```

### 4.5 Vue Django — squelette

```python
# apps/api/apps/recommendations/views.py (ajout à l'existant)
from django.db import transaction, IntegrityError
from rest_framework.response import Response
from rest_framework import status as http_status
from rest_framework.views import APIView

from apps.core.permissions import IsAuthenticatedAndActive, IsStudent, IsPathAdmin
from apps.audit.utils import record_audit, AuditResult
from apps.professions.models import Profession
from .models import RecommendationReview
from .serializers import (
    RecommendationReviewCreateSerializer,
    RecommendationReviewResponseSerializer,
    RecommendationReviewAdminSerializer,
)

class RecommendationReviewCreateView(APIView):
    permission_classes = [IsAuthenticatedAndActive, IsStudent]

    def post(self, request):
        serializer = RecommendationReviewCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        slug = serializer.validated_data["profession_slug"]
        try:
            profession = Profession.objects.get(slug=slug, is_active=True)
        except Profession.DoesNotExist:
            return Response(
                {"detail": "Profession introuvable."},
                status=http_status.HTTP_404_NOT_FOUND,
            )

        try:
            with transaction.atomic():
                review = RecommendationReview.objects.create(
                    student=request.user,
                    profession=profession,
                    reason=serializer.validated_data["reason"],
                    comment=serializer.validated_data.get("comment"),
                )
                record_audit(
                    action="recommendation_review_requested",
                    result=AuditResult.SUCCESS,
                    actor=request.user,
                    subject=review,
                    metadata={
                        "profession_slug": slug,
                        "reason": review.reason,
                    },
                )
        except IntegrityError:
            return Response(
                {"detail": "Une demande de revue existe déjà pour ce métier."},
                status=http_status.HTTP_409_CONFLICT,
            )

        # TODO(story-8-1): send confirmation email to student
        return Response(
            RecommendationReviewResponseSerializer(review).data,
            status=http_status.HTTP_201_CREATED,
        )


class RecommendationReviewAdminListView(APIView):
    permission_classes = [IsAuthenticatedAndActive, IsPathAdmin]

    def get(self, request):
        reviews = (
            RecommendationReview.objects.filter(status=RecommendationReview.Status.PENDING)
            .select_related("student", "profession")
            .order_by("-created_at")
        )
        serializer = RecommendationReviewAdminSerializer(reviews, many=True)
        return Response({"results": serializer.data})
```

### 4.6 Serializers Django — squelette

```python
# apps/api/apps/recommendations/serializers.py
from rest_framework import serializers
from .models import RecommendationReview

class RecommendationReviewCreateSerializer(serializers.Serializer):
    profession_slug = serializers.SlugField()
    reason = serializers.ChoiceField(choices=RecommendationReview.Reason.choices)
    comment = serializers.CharField(max_length=500, required=False, allow_null=True, allow_blank=True)

class RecommendationReviewResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecommendationReview
        fields = ["id", "status"]

class RecommendationReviewAdminSerializer(serializers.ModelSerializer):
    profession_slug = serializers.CharField(source="profession.slug", read_only=True)
    student_id = serializers.CharField(source="student.id", read_only=True)

    class Meta:
        model = RecommendationReview
        fields = ["id", "profession_slug", "student_id", "reason", "comment", "status", "created_at"]
```

### 4.7 URLs Django

```python
# apps/api/apps/recommendations/urls.py — MODIFIER, ajouter à l'existant
from django.urls import path
from .views import RecommendationsView, RecommendationReviewCreateView, RecommendationReviewAdminListView

app_name = "recommendations"

urlpatterns = [
    # Existing (Story 3.4)
    path("students/me/recommendations/", RecommendationsView.as_view(), name="student-recommendations"),
    # Story 3.7
    path("students/me/recommendation-reviews/", RecommendationReviewCreateView.as_view(), name="review-create"),
    path("admin/recommendation-reviews/", RecommendationReviewAdminListView.as_view(), name="admin-review-list"),
]
```

### 4.8 Hook TanStack Query — squelette

```typescript
// apps/web/src/hooks/useRequestRecommendationReview.ts
import { useMutation } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api/client";
import { readCsrfCookie } from "@/lib/api/client";

type Reason = "ne_correspond_pas" | "choquant_inapproprie" | "autre";

interface ReviewPayload {
  profession_slug: string;
  reason: Reason;
  comment?: string | null;
}

interface ReviewResponse {
  id: string;
  status: string;
}

async function submitReviewRequest(payload: ReviewPayload): Promise<ReviewResponse> {
  const csrfToken = readCsrfCookie() ?? undefined;
  return apiFetch<ReviewResponse>("/api/v1/students/me/recommendation-reviews/", {
    method: "POST",
    body: payload,
    csrfToken,
  });
}

export function useRequestRecommendationReview() {
  return useMutation({
    mutationFn: (payload: ReviewPayload) => submitReviewRequest(payload),
  });
}
```

### 4.9 Intégration dans FicheMetier

**MODIFIER `FicheMetier.tsx`** : ajouter `ReviewRequestButton` en pied de fiche, à côté de `ReportErrorButton` (déjà intégré en 3.8).

```tsx
// Dans FicheMetierDesktop et FicheMetierMobile, section pied de fiche :
<div className="flex flex-wrap gap-3 pt-4 border-t border-border-subtle">
  <ReportErrorButton professionSlug={profession.slug} professionName={profession.name} />
  {score !== undefined && (
    <ReviewRequestButton
      professionSlug={profession.slug}
      professionName={profession.name}
      hasScore={score !== undefined}
    />
  )}
</div>
```

**NE PAS modifier `FicheMetierPrint`** — pas de CTA interactifs en impression (AC1).

### 4.10 Test pattern frontend

```typescript
// apps/web/src/components/professions/__tests__/ReviewRequestButton.test.tsx
// Même structure que ReportErrorButton.test.tsx
// Mocker ReviewRequestForm pour éviter les crashes jsdom du Select Radix
// Tester : open/close, reviewRequested state, absente sans hasScore, absente en print
```

### 4.11 Décisions design verrouillées

- **Un seul signalement par student × profession** (contrainte DB `unique_together`) — le backend retourne 409 si doublon. Le front utilise l'état session pour éviter de re-render le bouton comme cliquable.
- **Formulaire minimaliste** — 1 champ obligatoire, 1 optionnel. Pas de screenshot, pas de formulaire long.
- **Pas de notification admin en sprint 6** — traitement différé à Epic 9.
- **Email différé** — laisser un TODO(story-8-1) dans la vue Django.
- **`profession_slug` dans le POST body**, pas dans l'URL — le student endpoint est `/students/me/recommendation-reviews/` (pas de slug dans l'URL car ce n'est pas une sous-resource de profession — c'est une action du student).

### 4.12 Fichiers à créer / modifier

**CRÉER :**
- `apps/api/apps/recommendations/models.py` — compléter (était vide)
- `apps/api/apps/recommendations/migrations/0001_recommendation_review.py`
- `apps/api/apps/recommendations/serializers.py`
- `apps/api/apps/recommendations/tests/test_reviews.py`
- `apps/web/src/components/professions/ReviewRequestButton.tsx`
- `apps/web/src/components/professions/ReviewRequestForm.tsx`
- `apps/web/src/hooks/useRequestRecommendationReview.ts`
- `apps/web/src/components/professions/__tests__/ReviewRequestButton.test.tsx`
- `apps/web/src/components/professions/__tests__/ReviewRequestForm.test.tsx`

**MODIFIER :**
- `apps/api/apps/recommendations/views.py` — ajouter les 2 nouvelles vues (existant = RecommendationsView Story 3.4)
- `apps/api/apps/recommendations/urls.py` — ajouter les 2 nouvelles routes
- `apps/web/src/components/professions/FicheMetier.tsx` — intégrer ReviewRequestButton en pied de fiche

**NE PAS MODIFIER :**
- `apps/api/apps/professions/` — tout est déjà fait en 3.8
- `apps/api/apps/recommendations/services/` — scoring service non touché
- `ScoreVocationnel` composant — pas de bouton revue sur la card liste, seulement sur la fiche détaillée

### 4.13 Learnings de 3.8 à appliquer

1. **`transaction.atomic()` wrapping create + audit_log** — pour cohérence si l'audit échoue.
2. **Tests backend marqués `@pytest.mark.postgresql_only`** — la contrainte `unique_together` requiert PostgreSQL pour les vrais tests de contrainte.
3. **Mocker `ReviewRequestForm` dans les tests de `ReviewRequestButton`** — les composants Radix Select crashent jsdom. Tester le formulaire en isolation dans `ReviewRequestForm.test.tsx`.
4. **`useIsMobile()` avec `useSyncExternalStore`** — pattern déjà établi dans `ReportErrorButton.tsx`, réutiliser tel quel.
5. **Toast stateful** — `useToast()` hook local avec `useRef` pour le timer, pattern établi dans `ReportErrorButton.tsx`.
6. **`useEffect` cleanup** — clearTimeout dans le return du useEffect pour éviter les memory leaks.
7. **`QueryClientProvider` dans les tests FicheMetier** — les tests existants ont déjà ce wrapper, ne pas casser.

### 4.14 Permissions existantes (réutiliser)

Les permissions `IsAuthenticatedAndActive`, `IsStudent`, `IsPathAdmin` existent dans `apps/api/apps/core/permissions.py` — ne pas recréer.

### 4.15 Pattern ULID

Même pattern que `ProfessionReport` en 3.8 :
```python
from python_ulid import ULID
id = models.CharField(
    primary_key=True,
    max_length=32,
    default=lambda: f"rev_{ULID()}",
    editable=False,
)
```

### 4.16 Pyproject.toml — ruff ignores

Les fichiers `recommendations/**` auront probablement les mêmes warnings Django (RUF012 pour `permission_classes`, `fields`). Ajouter dans `[tool.ruff.lint.per-file-ignores]` :

```toml
"apps/recommendations/**" = ["RUF012", "DJ001"]
```

---

## 5. References

- **Epic 3** : `_bmad-output/planning-artifacts/epics/epic-3-recommandation-vocationnelle-premier-aha.md` § Story 3.7
- **Story 3.8** : `3-8-signaler-erreur-fiche-metier.md` — modèle exact à suivre
- **Story 3.6** : Explicabilité — mentionne "Demander une revue humaine" (lien CTA vers cette story)
- **Story 3.12** : `FicheMetier` — intègre ce composant en pied de fiche
- **Epic 9** : interface admin modération — traitement des demandes de revue
- **Story 8.1** : email transactionnel — confirmation email (différé)
- **Story 1.13** : journal audit
- **PRD** : FR23 (revue humaine recommandation, RGPD art. 22)

---

## 6. Dev Agent Record

### Agent Model Used
claude-sonnet-4-6

### Completion Notes List

- **T1**: `RecommendationReview` model dans `recommendations/models.py` avec `Reason` (3 choix), `Status` enum. Contrainte `UniqueConstraint(student, profession)` (409 si doublon). Migration `0001`. Serializers create/response/admin. Vues `RecommendationReviewCreateView` (IsStudent) et `RecommendationReviewAdminListView` (IsPathAdmin). Audit log `recommendation_review_requested`. TODO(story-8-1) email laissé dans la vue. 17 tests pytest marqués `postgresql_only` dans `test_reviews.py`.
- **T2**: Hook `useRequestRecommendationReview` (TanStack Query mutation, CSRF). `ReviewRequestForm` avec Select shadcn obligatoire, Textarea 500 chars avec compteur, validation inline. `ReviewRequestButton` avec toast stateful (4s, `aria-live="polite"`), état `reviewRequested` session-local, dialog desktop / sheet mobile (via `useIsMobile` avec `useSyncExternalStore`). Intégré en pied de `FicheMetierMobile` et `FicheMetierDesktop` (absent de `FicheMetierPrint`). Bouton non rendu si `!hasScore`.
- **T3**: 20 tests frontend (10 `ReviewRequestButton` + 10 `ReviewRequestForm`). 501/504 tests passent (+20 tests nets, 3 failures préexistantes hors scope).

### File List

- `apps/api/apps/recommendations/models.py` — ajout `RecommendationReview`
- `apps/api/apps/recommendations/migrations/0001_recommendation_review.py` — migration
- `apps/api/apps/recommendations/migrations/__init__.py` — init
- `apps/api/apps/recommendations/serializers.py` — 3 serializers
- `apps/api/apps/recommendations/views.py` — ajout 2 vues review
- `apps/api/apps/recommendations/urls.py` — ajout 2 routes review
- `apps/api/apps/recommendations/tests/test_reviews.py` — 17 tests backend
- `apps/api/pyproject.toml` — ruff per-file-ignores recommendations app
- `apps/web/src/hooks/useRequestRecommendationReview.ts` — hook mutation
- `apps/web/src/components/professions/ReviewRequestForm.tsx` — formulaire
- `apps/web/src/components/professions/ReviewRequestButton.tsx` — bouton + dialog/sheet
- `apps/web/src/components/professions/FicheMetier.tsx` — intégration pied de fiche
- `apps/web/src/components/professions/__tests__/ReviewRequestButton.test.tsx` — 10 tests
- `apps/web/src/components/professions/__tests__/ReviewRequestForm.test.tsx` — 10 tests

### Change Log

- 2026-06-21 — Story 3.7 implémentée : backend RecommendationReview + endpoints + audit log ; frontend ReviewRequestButton + ReviewRequestForm + hook. 501/504 tests passent (+20 nets, 3 failures préexistantes).

### Debug Log

- `window.matchMedia` non disponible dans jsdom → même fix que 3.8 : `Object.defineProperty(window, "matchMedia", {...})` dans `beforeEach`.
- Tests de succès async : nécessitent `await waitFor(() => screen.getByTestId("submit-btn"))` avant de cliquer Submit, pour attendre que le Dialog soit monté dans le DOM.
- Migration utilise `UniqueConstraint` (new style) + `constraints` dans Meta au lieu de `unique_together` (old style) pour cohérence.
