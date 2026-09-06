# Story 5.11 : Composant `PaywallContextuel`

**Status:** done

## 1. User Story

As a développeur Path-Advisor,
I want un composant `PaywallContextuel` qui s'affiche quand un user free tente d'accéder à une feature premium,
So that le passage premium soit déclenché de manière contextuelle, non agressive (UX-DR15).

## 2. Scope decisions

- **Sheet, pas un nouveau pattern.** Réutilise le pattern Sheet-bottom déjà établi (`<SendOutreachButton>`, `<EcoleRespondForm>`) plutôt que d'introduire un 3ème type de modal dans le design system.
- **CTA primary = lien vers `/premium`**, pas un checkout inline. La vraie logique Stripe (`<PremiumCheckoutButton>`) vit déjà sur `/premium` — dupliquer cette logique dans un composant générique de paywall aurait été un risque (deux endroits à maintenir pour le même flow de paiement).
- **Cooldown implémenté comme "bypass direct" plutôt que "silence".** Après un "Plus tard", un nouveau tap sur le déclencheur ne réaffiche pas le Sheet — il navigue directement vers `/premium`. Interprétation choisie pour l'AC "évite que le paywall réapparaisse à chaque tap" : l'utilisateur qui retente clairement l'action gagne du temps au lieu de revoir la même pitch.
- **Premier usage réel : `<OutreachSection>` (Story 5.4).** Remplace le lien ad-hoc "Passe en premium" documenté à l'époque comme "paywall simplifié — le vrai composant est la Story 5.11".

## 3. Acceptance Criteria

**AC1 — Rendu**
**Given** le composant est implémenté
**When** je l'instancie avec props (`feature`, `title`/`description` (calqués sur le `context`), `benefits[]`)
**Then** il rend un Sheet avec titre contextuel, description (1-2 phrases), 2-3 bénéfices, CTA primary "Passer en premium — 10,99 €/mois", CTA secondary "Plus tard"
→ Implémenté tel quel.

**AC2 — Ton anti-urgence**
**Given** la conformité émotionnelle
**When** le composant s'affiche
**Then** il ne crie jamais, ne culpabilise pas, ton factuel
→ Implémenté par construction : le composant n'a aucune copie hardcodée alarmiste, tout le texte vient des props fournies par l'appelant (`OutreachSection`'s copy factuelle, testée explicitement pour l'absence de "DERNIÈRE CHANCE"/"tu rates").

**AC3 — Cooldown**
**Given** un user free clique "Plus tard"
**When** le composant se ferme
**Then** retour à la navigation précédente sans pénalité + cooldown 1×/session/feature
→ Implémenté : `sessionStorage` (pas `localStorage` — nouvelle session voit à nouveau le paywall).

## 4. Out of scope (deferred)

- Un second point d'intégration au-delà de `<OutreachSection>` (chaque future feature premium adoptera `<PaywallContextuel>` à son propre rythme — pas un "grand remplacement" de tous les upsells existants dans cette story).
- Variante "carte" inline (l'AC accepte "une carte ou un Sheet" — Sheet suffit, cohérent avec le reste de l'app).

## 5. Review Findings

**Frontend (uniquement — aucun changement backend) :**
- `<PaywallContextuel>` (nouveau, `components/features/premium/`) : props `feature`/`title`/`description`/`benefits`/`children` (trigger).
- `<OutreachSection>` : remplace le lien ad-hoc par `<PaywallContextuel feature="envoi-anticipe" ...>`.
- **Vérifié :** 8 nouveaux tests (rendu, CTA/prix exact, absence de copie alarmiste, cooldown sessionStorage) + 4 tests `OutreachSection` mis à jour (le trigger n'est plus un `<a>` mais un déclencheur de Sheet), suite complète 827 passed (12 échecs pré-existants non liés, même chiffre que les stories précédentes), tsc/eslint clean.
- Smoke-check Docker : `/schools` répond (redirect anonyme attendu, pas de crash serveur après rebuild `.next`).
