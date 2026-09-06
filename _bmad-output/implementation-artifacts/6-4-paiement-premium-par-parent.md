# Story 6.4 : Paiement premium par parent au bénéfice élève

**Status:** done

## 1. User Story

As a parent,
I want souscrire à l'abonnement premium 10,99 €/mois au bénéfice de mon enfant,
So that mon enfant accède aux features premium sans avoir à payer lui-même (FR42).

## 2. Scope decisions

- **`client_reference_id` reste toujours le bénéficiaire**, jamais le payeur. Le webhook Stripe (`SubscriptionService._resolve_user`) n'a donc besoin d'aucune logique spéciale pour "qui paie" — c'était déjà correctement découplé avant cette story. Le nouveau paramètre `metadata` (Stripe echo verbatim sur `checkout.session.completed`) porte `paid_by_user_id` uniquement quand un `beneficiary` distinct est passé à `BillingService.create_checkout_session`.
- **Un seul nouveau champ** : `Subscription.paid_by` (FK nullable, `SET_NULL`). Pas de nouvelle table de mapping — un abonnement n'a qu'un seul payeur potentiel à la fois, cohérent avec le modèle `Subscription` existant (1 ligne par bénéficiaire).
- **Pas d'historique des paiements (factures Stripe).** Aucune intégration de listing de factures Stripe n'existe nulle part dans ce codebase — même pour la propre souscription d'un élève. En construire une pour ce seul flow parent serait une nouvelle surface d'API Stripe non amortie ailleurs ; l'AC "Mes abonnements" est satisfaite avec le statut courant + prochaine échéance (déjà tout ce que `SubscriptionStatusView` expose pour soi-même).
- **Annulation** = réutilisation directe de `SubscriptionService.request_cancellation(user=student)`, déjà "impact uniquement à la fin de la période payée" par construction (Story 5.3) — rien de spécifique à 6.4 à y ajouter, seulement l'autorisation parent→enfant via `resolve_linked_child`.

## 3. Acceptance Criteria

**AC1 — CTA**
**Given** je suis sur mon dashboard parent et l'élève est en tier `free`
**When** je consulte la section "Abonnement de mon enfant"
**Then** je vois un CTA "Passer mon enfant en premium — 10,99 €/mois"
→ Implémenté : `<ChildSubscriptionSection>`.

**AC2 — Checkout**
**Given** je clique sur le CTA
**When** je suis redirigé vers Stripe Checkout
**Then** le paiement est associé à mon compte parent mais le bénéficiaire est l'`user_id` enfant
**And** après paiement, le tier de mon enfant passe à `premium`
→ Implémenté : `client_reference_id=student.id`, `customer_email=parent.email`, `metadata={"paid_by_user_id": parent.id}`.

**AC3 — Gestion**
**Given** je peux gérer l'abonnement
**When** je vais dans "Mes abonnements"
**Then** je vois le statut + la prochaine échéance
**And** je peux annuler (impact uniquement à la fin de la période payée)
→ Implémenté (historique des paiements différé, §2).

**AC4 — Audit**
**Given** un paiement parent → enfant est traité
**When** il est traité
**Then** une trace lie `paying_user_id` (parent) à `beneficiary_user_id` (enfant)
→ Implémenté : `billing.premium_purchased_by_parent` (en plus du `billing.checkout_session_created` existant, déjà enrichi de `beneficiary_user_id`).

## 4. Out of scope (deferred)

- Historique des factures Stripe (aucune intégration existante à réutiliser).
- Plusieurs payeurs concurrents pour un même bénéficiaire (le dernier checkout gagne, comme pour le self-checkout — comportement de merge déjà existant, Story 5.2).

## 5. Review Findings

**Backend :**
- `Subscription.paid_by` (nouveau champ, migration `0004`).
- `PaymentProvider.create_checkout_session` : nouveau paramètre `metadata` (interface + implémentation Stripe).
- `BillingService.create_checkout_session` : nouveau paramètre `beneficiary` (rétrocompatible — tous les appels existants passent `beneficiary=None`).
- `SubscriptionService._on_checkout_completed` : lit `metadata.paid_by_user_id`, l'enregistre sur `Subscription.paid_by`, logge `billing.premium_purchased_by_parent` si présent.
- `apps/family/services/parent_billing.py` (nouveau) : `create_child_checkout_session`, `get_child_subscription_status`, `cancel_child_subscription` — chacun ré-autorise via `resolve_linked_child`.
- 3 nouveaux endpoints `family` : checkout-session / subscription / subscription/cancel, scopés `IsParent`.
- **Vérifié :** 9 nouveaux tests + 112 tests `family`+`billing` au total (SQLite + Postgres réel), suite complète 1358 passed (0 régression), ruff/`assert_rbac_declared`(277)/`manage.py check`/migrations clean.

**Frontend :**
- `lib/api/parent.ts` : `ChildSubscriptionStatus` + 3 nouvelles fonctions.
- `<ChildSubscriptionSection>` (nouveau), intégré dans `/parent/enfants/[studentId]`.
- **Vérifié :** 4 nouveaux tests, suite complète 840 passed (12 échecs pré-existants non liés, même chiffre que toutes les stories précédentes), tsc/eslint clean.

**Smoke test Docker (réel, end-to-end) :** checkout créé avec `client_reference_id=enfant`, `metadata.paid_by_user_id=parent` → webhook simulé → `Subscription.paid_by` correctement enregistré → `get_child_subscription_status` renvoie `paid_by_parent=true` → annulation programmée sans perte de premium → trace d'audit `billing.premium_purchased_by_parent` confirmée avec les deux ids. Données de test nettoyées après vérification.
