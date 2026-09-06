# Story 5.12 : Composant `EcoleResponseFlow`

**Status:** done

## 1. User Story

As a développeur Path-Advisor,
I want un composant `EcoleResponseFlow` qui affiche un profil élève + permet à l'école de répondre en 3 actions,
So that l'espace école soit cohérent et efficace pour Mme Garcia (UX-DR22).

## 2. Scope decisions

- **Extraction, pas reconstruction.** Les Stories 5.6/5.7 avaient déjà tout le nécessaire directement inline dans `/ecole/outreach/[id]/page.tsx` (header, sections, footer 3-actions). Cette story extrait ce contenu en un composant réutilisable `<EcoleResponseFlow>` plutôt que de repartir de zéro — la page devient une simple coquille de data-fetching.
- **Props réduites aux données réelles.** La liste de props de l'épic (`studentProfile` avec moyennes/spés/appréciations enseignants, un score de compatibilité) suppose des données qui n'existent nulle part dans ce codebase — déjà constaté et documenté à la Story 5.6 §2 (le modèle `User` n'a ni prénom/nom, ni synthèse académique, aucun score élève↔école n'a jamais été construit). Le composant prend une seule prop `outreach` reflétant ce que le backend renvoie réellement : âge (pas nom), pas de ligne de score (omise, pas simulée).
- **Raccourcis clavier dans `<EcoleRespondForm>`, pas dupliqués dans `<EcoleResponseFlow>`.** Les 3 actions (et donc leurs raccourcis `i`/`n`/`e`) appartiennent déjà à `EcoleRespondForm` (Story 5.7) — les y implémenter directement évite un système de ref/callback entre les deux composants pour un gain nul.
- **Message RBAC toujours affiché**, pas conditionnel : il n'y a de toute façon aucune autre donnée à cacher (les autres recos/écoles ne sont jamais envoyées par le backend — décision de scope de la Story 5.4).

## 3. Acceptance Criteria

**AC1 — Rendu**
**Given** le composant est implémenté
**When** je l'instancie avec ses props
**Then** il rend header (âge + date d'envoi — pas de score, cf. §2) + section "Profil scolaire" (âge — pas de moyennes/spés/appréciations, cf. §2) + section "Motivation" + section "Métier & parcours visés" + footer (3 boutons via `EcoleRespondForm`, ou le résumé en lecture seule une fois répondu)
→ Implémenté avec les réductions de scope documentées ci-dessus.

**AC2 — Frontières RBAC**
**Given** les frontières RBAC sont strictes
**When** je consulte un profil reçu
**Then** je ne vois PAS les autres écoles ciblées ni les autres recos vocationnelles
**And** un message rappelle "Tu vois uniquement ce que l'élève a choisi de partager avec toi"
→ Implémenté : message toujours visible ; l'absence des autres données est structurelle (rien à filtrer, le backend ne les envoie jamais).

**AC3 — Densité desktop**
**Given** la densité desktop (école = desktop primaire)
**When** je consulte le composant sur écran 1024+ px
**Then** layout en 2 colonnes (profil à gauche, actions à droite)
**And** raccourcis clavier supportés (`i`/`n`/`e`)
→ Implémenté : `grid lg:grid-cols-2` (1024px = breakpoint Tailwind `lg`) ; raccourcis dans `EcoleRespondForm`.

## 4. Out of scope (deferred)

- Toute donnée de profil scolaire au-delà de l'âge (aucune synthèse académique n'existe — cf. Story 5.6 §2, non reconstruit ici).
- Un score de compatibilité élève↔école (n'existe nulle part — cf. Story 5.6 §2).

## 5. Review Findings — clôture de l'Epic 5

**Frontend (uniquement — aucun changement backend) :**
- `<EcoleResponseFlow>` (nouveau, `components/features/outreach/`) : compose header/sections/2-col/footer.
- `<EcoleRespondForm>` : ajout des raccourcis clavier `i`/`n`/`e` sur l'étape "choose" (ignorés pendant la saisie dans un textarea/input, et pendant un envoi en cours).
- `/ecole/outreach/[id]/page.tsx` simplifiée : coquille de data-fetching autour de `<EcoleResponseFlow>`.
- **Vérifié :** 5 nouveaux tests `EcoleResponseFlow` (rendu des sections, message RBAC, footer 3-actions, résumé lecture seule, raccourci clavier `i`) + test de page mis à jour (mock du composant enfant), 31 tests dans `outreach`/`ecole` au total, suite complète 832 passed (12 échecs pré-existants non liés, même chiffre que toutes les stories précédentes de l'épic), tsc/eslint clean. Smoke-check Docker : `/ecole/outreach` répond correctement après rebuild `.next` (redirect anonyme attendu, pas de crash).

---

**Epic 5 (Premium B2C & Envoi Anticipé Biface) — clôturé.** 12 stories (5.1 à 5.12) livrées et mergées dans `main` : intégration Stripe, tiers d'abonnement, souscription premium, envoi anticipé (création, modération, réception école, réponse école, propagation stat temps réel, historique, reporting), et les 2 composants génériques (`PaywallContextuel`, `EcoleResponseFlow`).
