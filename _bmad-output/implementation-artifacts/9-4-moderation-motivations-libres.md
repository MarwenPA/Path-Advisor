# Story 9.4 — Modération a priori (motivations élèves + commentaires écoles)

Statut : review · Epic 9 · 2026-09-26

## 1. User Story

As a admin Path-Advisor, I want modérer a priori les motivations libres des élèves (et, par l'amendement de la revue Epic 8, les commentaires libres des écoles), So that les contenus inappropriés / discriminatoires / les données personnelles tierces soient filtrés avant d'atteindre leur destinataire (FR50).

## 2. Décisions de périmètre

1. **Réutilisation intégrale de la machine 5.5** : `approve_early_outreach_motivation` / `reject_early_outreach_motivation` (état, emails élève « approuvée »/« refusée + corrige et re-soumets ») appelés tels quels par l'API — l'écran Django admin interim de 5.5 est remplacé par la vraie UI que son propre docstring promettait à 9.4. Ajout : `rejection_category` typée (contenu inapproprié / données tierces / discrimination / autre), exigée par l'AC, stockée à côté du motif libre.
2. **SLA « 24 h ouvrées » réellement ouvré** : `business_hours_since` (heures pleines lun-ven) — un dossier soumis vendredi 18 h n'est pas « en retard » lundi 10 h. Exposé par ligne (`business_hours_age`, `overdue`) + compteur global.
3. **Pré-screening = une AIDE, jamais une décision** (AC) : `prescreen_text` détecte les PII (email, téléphone FR, URL) et une liste VOLONTAIREMENT COURTE de marqueurs haine/violence — une longue blocklist pourrit et sur-flagge ; l'humain lit de toute façon. Aucun auto-refus, la note l'affiche dans l'UI.
4. **Amendement (revue Epic 8, P2-5) — commentaires écoles** : un commentaire de staff non vide entre en modération a priori (`comment_status=pending`) ; **l'email « réponse école » part immédiatement SANS le commentaire** (l'information de la réponse ne doit pas attendre — les templates 8.4 ne rendent plus `response.comment`) ; in-app, `/mes-envois` sert un `comment` vide + `comment_pending=true` tant que non approuvé ; un commentaire rejeté ne surface JAMAIS (flag terminal, pas de faux espoir). L'école n'est pas notifiée d'un rejet (pas de canal de réponse — consigné). Commentaire vide = auto-approuvé (rien à modérer).
5. **Audit** : `moderation.motivation_approved|rejected`, `moderation.school_comment_approved|rejected` — acteur, école, transactionnel.
6. L'UI élève de `/mes-envois` n'affiche pas encore d'indicateur « message en cours de relecture » — le flag `comment_pending` est exposé par l'API pour la story front qui le voudra (consigné, hors périmètre back-office).

## 3. Résultats (implémentation)

**Livré.**

- **Modèles** : `EarlyOutreachRequest.rejection_category` ; `EarlyOutreachResponse.comment_status/comment_moderated_by/at` (migration outreach 0004) ; gate posé dans `respond_to_outreach_request` ; serializer élève gaté (`comment` vide si non approuvé + `comment_pending`) ; templates 8.4 sans le commentaire.
- **API `IsPathAdmin`** : `GET /admin/moderation/motivations/` et `/school-comments/` (plus vieux d'abord, âge ouvré, overdue >24 h, prescreen par ligne, compteurs) ; `POST {id}/approve|reject` sur les deux files (reject motivation = catégorie + motif OBLIGATOIRES ; garde d'état 409 sur double action).
- **Front** : `/admin/moderation` — 2 onglets avec compteurs et badges SLA, note « décision toujours humaine » permanente, chips de pré-screening, lecture plein-largeur, refus motivation avec catégorie+motif désarmé tant que vide.
- **Tests** : 8 backend (prescreen pur, file SLA ouvrée+prescreen, approve = sémantique 5.5 (déblocage + email), reject double-garde + catégorie stockée + 409, 403 non-admin, gate commentaire bout-en-bout (email sans commentaire → caché in-app → file → approve → visible), rejet jamais montré + 409, vide auto-approuvé) + 3 front. Fast lane **1585**, lane RLS **155**, web **131 fichiers** verts, RBAC 316.
- **Preuve live** (session MFA réelle) : file motivations avec `prescreen.pii=['telephone']` → reject sans catégorie **400** → reject typé `donnees_tierces` **200** ; réponse école avec commentaire → **email Mailpit SANS le commentaire** (CTA présent) → file commentaires avec prescreen → approve **200**.
