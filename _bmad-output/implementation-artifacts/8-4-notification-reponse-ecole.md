# Story 8.4 : Notification "réponse école" envoi anticipé

**Status:** review

## 1. User Story

As a élève premium,
I want recevoir une notification email quand une école a répondu à mon envoi anticipé,
So that je puisse réagir rapidement (FR47 + lien avec Story 5.8).

## 2. Constat d'inventaire — la story était à moitié faite, et à moitié fausse

L'email « une école a répondu » existait déjà (Story 5.7, migré vers l'outbox en 8.1) — mais il partait **directement** à `send_transactional` : il **contournait les préférences** de notification et n'avait **pas le footer légal**. La 8.4 consiste précisément à le faire entrer dans le rang : routage par `notify()` (catégorie `school_responses`), qui applique l'opt-out au point d'envoi et injecte les liens légaux.

## 3. Décisions

1. **Périmètre engine** : seul `send_school_responded_email` devient une notification de catégorie. Les autres emails outreach (créneaux d'entretien, avis au staff école) restent des envois transactionnels de workflow — étapes d'un flux initié par l'élève, pas une catégorie désabonnable. Frontière documentée dans le docstring.
2. **AC3 « reste visible in-app » est structurel** : `respond_to_outreach_request` persiste la réponse **avant** tout appel email ; `/mes-envois` (5.9) lit cette table. Opt-out → zéro email, la réponse est là quand même — testé.
3. **Ton diplomatique = lint exécutable** (même approche que UX-DR28 en 8.3) : la variante `not_aligned` rendue (sujet+txt+html) interdit « mauvaise nouvelle », « malheureusement », « refus », « rejet », « échec », « pas retenu » — et **exige** la proposition d'alternatives (« explorer d'autres écoles… profil similaire ») + le CTA « Voir la réponse ». Copy réécrite : « C'est une information utile, pas un verdict ». Le « ! » du sujet `interested` retiré au passage.
4. CTA « Voir la réponse » → `/mes-envois/{id}` (page 5.9 existante) ; alternatives → `/schools` (catalogue 4.14).

## 4. Résultats (2026-09-26)

- Tests : ton linté sur les 3 variantes + footer légal partout + opt-out (réponse persistée, zéro email, zéro ligne outbox) + chemin nominal (email avec footer et CTA). Suite outreach 62 passants.
- **Preuve vivante** : vraie réponse `not_aligned` via `respond_to_outreach_request` en conteneur → worker → Mailpit : sujet neutre (« …a répondu à ton envoi »), pas de « mauvaise nouvelle », alternatives présentes, CTA `/mes-envois/`, footer `/desinscription/`.
- Gates : lane rapide **1509**, lane RLS **154**, ruff/format propres, mypy baseline inchangée (21=21, zéro dans mes fichiers), RBAC **296**.
- Bavure corrigée en tête de branche : `celerybeat-schedule` (état runtime de pa-beat) avait été balayé par un `git add -A` — retiré du suivi et gitignoré.
