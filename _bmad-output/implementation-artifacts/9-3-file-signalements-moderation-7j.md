# Story 9.3 — File de signalements + workflow < 7 jours

Statut : review · Epic 9 · 2026-09-26

## 1. User Story

As a admin Path-Advisor, I want une file de signalements priorisée + un workflow de traitement sous 7 jours, So that les retours utilisateurs soient traités vite et le référentiel reste de qualité (FR49).

ACs : file ordonnée par âge + priorité, alerte si > 7 j non traité ; filtres par type ; ouverture = fiche concernée + contexte + message ; actions = corriger (lien 9.1/9.2), rejeter (motif), demander des précisions (notification) ; résolution → notification « la fiche que tu as signalée a été mise à jour » (si opt-in) + file mise à jour.

## 2. Décisions de périmètre

1. **Source = `ProfessionReport` (3.8), le seul flux de signalement existant.** L'AC mentionne « école obsolète » comme type — mais AUCUNE story n'a donné aux élèves un bouton de signalement d'école (3.8 ne couvre que les fiches métiers). La file traite ce qui existe ; le signalement d'écoles est une story candidate consignée (Epic 10 / backlog), pas un fantôme d'UI.
2. **Workflow** : `pending → resolved | dismissed | info_requested`. `dismissed` exige un motif (`admin_note`) ; `info_requested` exige un message envoyé à l'élève — le signalement RESTE dans la file (statut visible) car la balle revient côté admin après réponse de l'élève (MVP : l'élève répond en re-signalant ou par la fiche — pas de fil de discussion structuré, consigné). `resolved` porte `handled_by`/`handled_at` + note optionnelle.
3. **« > 7 jours » = calculé, jamais stocké** : `overdue = now - created_at > 7 j` exposé par l'API + badge UI + compteur en tête de file. Pas d'email d'alerte ops (l'AC dit « alerter », l'UI alerte ; un canal ops type Slack/email est du ressort de 9.6 monitoring — consigné).
4. **Notifications à l'élève via l'engine 8.2, nouvelle catégorie `report_updates`** (« Suivi de tes signalements ») : elle a désormais un émetteur, donc elle apparaît dans les réglages (règle 9.1/P2-4 : une catégorie n'est visible que si émettrice). Opt-out respecté par `notify()` — l'AC « si opt-in » est couvert par le modèle opt-out documenté 8.2 (activé par défaut, coupable). Deux templates lintés (`tone.py`) : `report_resolved` (« la fiche a été mise à jour », lien fiche) et `report_info_requested` (message de l'admin, ton calme). `dismissed` n'envoie RIEN (consigné : un rejet notifié sans canal de réponse frustre plus qu'il n'informe ; le motif reste en base pour le support).
5. **« Corriger la fiche »** = lien direct `/admin/metiers/{slug}` (9.1) depuis le panneau — pas de duplication d'édition dans la file.
6. **Audit** : `moderation.report_resolved|dismissed|info_requested` avec `handled_by` implicite (actor) et le motif dans metadata (borné).

## 3. Périmètre technique

- Modèle : `ProfessionReport` += `admin_note` (Text, blank), `handled_by` (FK SET_NULL), `handled_at` ; `Status` += `INFO_REQUESTED`. Migration.
- API `IsPathAdmin` : liste filtrée (`status`, `error_type`, tri âge asc = plus vieux d'abord, `overdue` par ligne + `overdue_count` global) ; détail (fiche + reporter + message) ; `POST {id}/resolve|dismiss|request-info`.
- Notifications : catégorie `report_updates` + 2 triplets de templates + branchement `notify()`.
- Front : `/admin/signalements` (file + filtres + badges âge/overdue, panneau détail avec les 3 actions + lien fiche).
- Tests : tri/overdue, transitions + garde motif/message, notifications outbox + opt-out, dismissed silencieux, catégorie visible réglages, lint de ton des 2 templates, RBAC.

## 4. Résultats (implémentation)

**Livré.**

- **Modèle** : `ProfessionReport` += `admin_note`/`handled_by`/`handled_at` + statut `info_requested` (migrations 0008/0009). Source unique = 3.8 ; le signalement d'écoles n'a pas de flux élève — consigné comme story candidate (§2.1).
- **Workflow** (`services/report_moderation.py`) : resolve (note optionnelle, **notifie** l'élève), dismiss (**motif obligatoire**, silencieux — §2.4), request-info (**message obligatoire**, notifié, reste dans la file) ; `handled_by/at` + audit `moderation.*` dans la transaction de chaque transition.
- **File** : plus vieux d'abord (SLA = jeu d'âge), `overdue` par ligne + `overdue_count` global (> 7 j calculé, jamais stocké), filtres statut/type, vue par défaut = actionnable (pending + info_requested).
- **Notifications** : nouvelle catégorie `report_updates` (« Suivi de tes signalements ») — émettrice dès sa naissance donc visible dans les réglages (règle 9.1/P2-4, testé : elle apparaît, `profile_completion` reste masquée) ; 2 triplets de templates lintés via `tone.py` partagé ; opt-out respecté par `notify()` (testé : le travail se fait, l'email non).
- **Front** : `/admin/signalements` — bannière SLA, badges âge/>7 j/précisions-demandées, « Corriger la fiche » → `/admin/metiers/{slug}` (9.1), rejet/précisions avec confirmation désarmée tant que le texte est vide.
- **Tests** : 9 backend (tri+overdue, 403, resolve→email+footer, opt-out, dismiss garde+silence, request-info notifie+reste en file, catégorie visible, lint ton ×2) + 3 front. Fast lane **1577**, lane RLS **155**, web 130 fichiers verts, RBAC 312.
- **Preuve live** (session MFA) : file `overdue_count=1` + ligne `overdue:true` (signalement vieilli 9 j) → dismiss sans motif **400** → resolve **200** → **Mailpit** : « Ta fiche signalée a été mise à jour — Agent·e de sécurité privée » au reporter réel.
