# Story 5.9 : Historique des envois anticipés côté élève

**Status:** done

## 1. User Story

As a élève,
I want consulter le statut et l'historique de tous mes envois anticipés,
So that je peux suivre mes démarches et planifier mes vœux Parcoursup (FR39).

## 2. Scope decisions

- **5 groupes, pas 6.** La Story 5.5 (motivation modérée) a introduit `pending_moderation`/`rejected` après que l'épic ait écrit ses 5 buckets ("En attente / Réponses positives / Réponses négatives / Entretiens demandés / Expirés"). Plutôt qu'ajouter un 6ème groupe, ces deux statuts sont pliés dans "En attente" — ce sont des sous-états de "pas encore répondu", pas une catégorie distincte du point de vue de l'élève.
- **Badge d'impact stat = `response.stat_delta`**, déjà exposé par le serializer de réponse depuis la Story 5.8 — aucun nouveau calcul ici, juste son affichage (`+15 pts` / `-15 pts` / `+7 pts`) sur chaque carte + dans la fiche détail.
- **Détail = un seul champ de plus que la liste** (`motivation_text`) — tout le reste (réponse, statut, école) était déjà exposé par `EarlyOutreachListSerializer`. Nouvelle vue dédiée `GET /outreach/requests/{id}/` plutôt que de gonfler la liste avec la motivation de chaque envoi (payload inutilement lourd pour un historique qui peut compter plusieurs dizaines de lignes).

## 3. Acceptance Criteria

**AC1 — Liste groupée**
**Given** je vais sur "Mes envois"
**When** la page s'affiche
**Then** je vois la liste de tous mes envois, regroupés par statut (En attente / Réponses positives / Réponses négatives / Entretiens demandés / Expirés)
**And** chaque envoi affiche école, métier visé, date d'envoi, statut, impact stat (badge "+ 14 pts" si applicable)
→ Implémenté : `/mes-envois` regroupe désormais en 5 sections, chaque carte affiche le badge de delta quand une réponse existe.

**AC2 — Fiche détail**
**Given** je tape sur un envoi
**When** la fiche détail s'ouvre
**Then** je vois ma motivation envoyée + la réponse de l'école (texte + action) + l'impact sur ma stat + un lien vers la fiche école
→ Implémenté : nouvelle page `/mes-envois/[id]` + endpoint `GET /outreach/requests/{id}/`.

**AC3 — Empty state**
**Given** je n'ai aucun envoi
**When** je consulte la page
**Then** un empty state explique "Tu n'as pas encore envoyé ton profil..."
**And** un CTA "Voir les écoles partenaires"
→ Déjà présent depuis la Story 5.4, inchangé.

## 4. Out of scope (deferred)

- Story 5.10 : reporting interne école (une vue agrégée côté école, pas côté élève).
- Un filtre/tri manuel sur `/mes-envois` (le groupement par statut suffit à l'AC ; un futur besoin de tri par date/école serait une itération séparée).

## 5. Review Findings

**Backend :**
- `EarlyOutreachListSerializer` : ajout de `school_slug` (lien vers la fiche école).
- `EarlyOutreachStudentDetailSerializer` (nouveau, hérite de la liste) : ajoute `motivation_text`.
- `EarlyOutreachDetailView` (nouveau) : `GET /outreach/requests/{id}/`, scopé `student=request.user`, 404 sinon (même convention que le reste de l'app).
- **Vérifié :** 49/49 tests (SQLite + Postgres réel), ruff/`assert_rbac_declared`(272)/`manage.py check`/migrations clean.

**Frontend :**
- `/mes-envois` réécrit : regroupement en 5 sections, `<StatDeltaBadge>` (nouveau, inline) sur chaque carte, lien vers `/mes-envois/[id]`.
- `/mes-envois/[id]` (nouveau) : motivation, réponse (texte + action), impact stat, lien vers `/schools/{slug}`.
- **Vérifié :** 8 tests `mes-envois` (2 nouveaux fichiers/cas ajoutés pour le groupement + la fiche détail), suite complète 820 passed (12 échecs pré-existants non liés, même chiffre que les stories précédentes), tsc/eslint clean.

**Smoke test Docker (réel) :** requête `responded`/`interested` avec motivation + commentaire → `EarlyOutreachStudentDetailSerializer` renvoie `motivation_text`, `school_slug`, et `response.stat_delta=15` correctement ; `EarlyOutreachListSerializer` omet bien `motivation_text` (payload de liste plus léger). Données de test nettoyées après vérification.
