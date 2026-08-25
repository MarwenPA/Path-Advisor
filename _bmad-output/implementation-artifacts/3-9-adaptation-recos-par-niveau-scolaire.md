# Story 3.9 — Adaptation des recommandations par niveau scolaire

**Epic:** 3 — Recommandation Vocationnelle (Premier Aha)
**Status:** ready-for-dev
**Sprint:** 6 (Recommandation vocationnelle)
**Story Key:** `3-9-adaptation-recos-par-niveau-scolaire`
**Estimation:** M (medium) — 3 layers: ai-service scorer + Django post-processing + frontend banner. ~1.5 j.

> Les recommandations tiennent déjà compte du niveau scolaire via `niveau_compatibility` (20% du score), mais les spécialités de l'élève ne contribuent pas encore au score, et la composition du Top 8 ne garantit pas que ≥60% des résultats soient compatibles avec le niveau déclaré. Cette story ajoute le feature `specialite_overlap` dans le scorer, un post-processing de seuil dans Django, et un bandeau contextuel frontend.

---

## 1. User Story

**As** an élève (Mehdi 3ème ou Sarah Terminale spé Maths+SVT),
**I want** que mes recos métiers soient adaptées à mon niveau scolaire et à mes spécialités,
**So that** mes recos soient cohérentes et actionnables (FR25).

---

## 2. Acceptance Criteria (BDD)

### AC1 — Seuil de compatibilité niveau (3ème → bac pro)

**Given** je suis Mehdi (`niveau = "college_3eme"`, `filiere = "bac_pro"`)
**When** le moteur calcule mon Top 8
**Then** au moins 5 professions sur 8 (≥60%) ont `"college_3eme"` dans leur `level_compatibility`
**And** si le score pur ne suffit pas à remplir le quota, les professions compatibles les mieux scorées remontent dans le Top 8

### AC2 — Spécialités contribuent au score

**Given** je suis Sarah (`niveau = "lycee_1ere_tle_general"`, `specialites = ["svt", "maths"]`)
**When** le moteur score les professions
**Then** les professions dont `signals_json.specialites` chevauche mes spécialités (`svt`, `maths`) obtiennent un score plus élevé (feature `specialite_overlap`, poids 15%)
**And** parmi deux professions à `passion_overlap` + `valeur_alignment` égaux, celle avec la meilleure correspondance de spécialités est classée plus haute

### AC3 — Recalcul après changement de niveau

**Given** je mets à jour mon niveau scolaire dans mon profil (Story 2.6 — déjà implémenté)
**When** je reviens sur "Mes métiers recommandés"
**Then** mes recos sont recalculées immédiatement (pas de cache — déjà le cas)
**And** si le post-processing de seuil a reordonné le Top 8, la réponse API inclut `niveau_adapted: true`
**And** le frontend affiche un bandeau informatif : _"Tes recos tiennent compte de ton niveau scolaire"_

### AC4 — Pas de régression si niveau non déclaré

**Given** un élève sans niveau déclaré (`niveau = ""` ou `null`)
**When** le moteur calcule son Top 8
**Then** les recos sont calculées normalement (passion + valeur + bulletin uniquement, ni spécialité ni seuil de niveau)
**And** la réponse inclut `niveau_adapted: false`
**And** le bandeau frontend N'est PAS affiché

### AC5 — Nouveau feature `specialite_overlap` dans les signaux contributifs

**Given** la réponse ai-service
**When** elle contient `signals_contributifs`
**Then** chaque occupation score a un signal `specialite_overlap` en plus des 4 existants
**And** le `model_version` passe à `"0.3.0-statistical"`
**And** `FEATURES` liste maintenant 5 features

### AC6 — Tests

**ai-service :**
- `_specialite_overlap` vide profil → 0.0
- `_specialite_overlap` sans chevauchement → 0.0
- `_specialite_overlap` chevauchement partiel → Jaccard correct
- `_specialite_overlap` case-insensitive (`SVT` == `svt`)
- `score_occupations` retourne bien 5 `SignalContributif` par profession (inclut `specialite_overlap`)
- Les poids sum = 1.0

**Django :**
- Post-processing: si niveau déclaré et 3 compatibles sur 8 → reordonné à 5 compatibles min
- Post-processing: si déjà ≥5 compatibles → inchangé, `niveau_adapted = False`
- Post-processing: si niveau non déclaré → inchangé, `niveau_adapted = False`
- `compute_recommendations()` retourne `niveau_adapted` dans sa réponse
- Vue retourne `niveau_adapted` dans le JSON

**Frontend :**
- `niveau_adapted: true` → bandeau affiché
- `niveau_adapted: false` → bandeau absent
- Bandeau absent si liste vide

---

## 3. Tasks / Subtasks

### T1 — ai-service : feature `specialite_overlap`

- [ ] Ajouter `_specialite_overlap(profile: dict, signals: dict) -> float` dans `statistical_scorer.py`
  - Jaccard sur `profile["specialites"]` vs `signals["specialites"]` (case-insensitive, stripped)
  - Même pattern que `_passion_overlap` / `_valeur_alignment`
- [ ] Intégrer dans `_WEIGHTS` et `score_occupations()`
  - Nouveaux poids : `passion_overlap=0.30`, `valeur_alignment=0.20`, `niveau_compatibility=0.15`, `specialite_overlap=0.15`, `bulletin_quality=0.20`
  - Ajouter `SignalContributif` pour `specialite_overlap` dans la liste des 5
- [ ] Bumper `MODEL_VERSION = "0.3.0-statistical"` et ajouter `"specialite_overlap"` à `FEATURES`
- [ ] Mettre à jour `test_statistical_scorer.py` : ajuster les poids attendus, ajouter les tests AC6 ai-service

### T2 — Django : post-processing seuil 60%

- [ ] Ajouter `_reorder_for_level_threshold()` dans `recommendation_service.py`
  - Signature : `(sorted_results, profession_by_id, niveau, threshold=0.6) -> tuple[list, bool]`
  - Si `niveau` vide : retourne `(sorted_results[:8], False)`
  - Sépare les professions compatibles / incompatibles avec le `niveau`
  - Si `len(compatible) >= ceil(8 * threshold)` (=5) : retourne inchangé, `False`
  - Sinon : prend les `compatible` + remplit avec les meilleures `incompatible` → Top 8 reordonné, `True`
- [ ] Modifier `compute_recommendations()` pour appeler ce helper après le tri
  - Retourner `{"results": [...], "niveau_adapted": bool}` au lieu de `list`
- [ ] Mettre à jour `RecommendationsView` pour lire `niveau_adapted` et l'inclure dans la réponse JSON
  - Réponse actuelle : `{"results": [...], "computed_at": "..."}` → ajouter `"niveau_adapted": bool`
- [ ] Mettre à jour `test_recommendations.py` : ajuster les tests qui vérifient la structure de réponse, ajouter les tests AC6 Django

### T3 — Frontend : bandeau et types

- [ ] Mettre à jour `recommendations.ts` : ajouter `niveau_adapted?: boolean` à `RecommendationsResponse`
- [ ] Mettre à jour `MesMetiersPage` (`mes-metiers/page.tsx`) : passer `niveauAdapted` à `MetiersList`
- [ ] Mettre à jour `MetiersList.tsx` : ajouter prop `niveauAdapted?: boolean`, afficher le bandeau si `true`
  - Bandeau : `<p className="mb-4 rounded-lg bg-blue-50 px-4 py-3 text-sm text-blue-800">Tes recos tiennent compte de ton niveau scolaire.</p>`
  - Rôle `role="status"` pour accessibilité
  - Positionné au-dessus de la liste

### T4 — Tests

- [ ] Tests Jest/RTL pour `MetiersList` : `niveauAdapted=true` → bandeau présent, `false` → absent
- [ ] Tests pytest Django (non-postgresql) pour le post-processing

---

## 4. Dev Notes

### 4.1 Architecture — layers concernés

```
ai-service/src/domain/recommendation/statistical_scorer.py  ← T1
apps/api/apps/recommendations/services/recommendation_service.py  ← T2
apps/api/apps/recommendations/views.py  ← T2
apps/web/src/lib/api/recommendations.ts  ← T3
apps/web/src/app/(authenticated)/mes-metiers/page.tsx  ← T3
apps/web/src/app/(authenticated)/mes-metiers/MetiersList.tsx  ← T3
```

### 4.2 Niveau vocabulary — valeurs connues

`StudentLevelProfile.level` (côté Django/ai-service profile) :
| Valeur | Signification |
|--------|---------------|
| `college_3eme` | Collège 3ème |
| `lycee_2nde` | 2nde (général/techno) |
| `lycee_1ere_tle_general` | 1ère / Terminale générale |
| `lycee_1ere_tle_techno` | 1ère / Terminale technologique |
| `lycee_1ere_tle_pro` | 1ère / Terminale pro |
| `postbac` | Post-bac |

`Profession.level_compatibility` (ArrayField) contient ces mêmes valeurs. La comparaison est case-insensitive + stripped (déjà le cas dans `_niveau_compatibility`).

### 4.3 Poids du scorer — migration de v0.2 → v0.3

| Feature | v0.2 | v0.3 |
|---------|------|------|
| `passion_overlap` | 35% | 30% |
| `valeur_alignment` | 25% | 20% |
| `niveau_compatibility` | 20% | 15% |
| `specialite_overlap` | — | 15% (NEW) |
| `bulletin_quality` | 20% | 20% |

Les tests existants dans `test_statistical_scorer.py` qui assertent des contributions de score précises vont échouer — c'est attendu. Les mettre à jour avec les nouveaux poids.

### 4.4 Pattern exact pour `_specialite_overlap`

```python
def _specialite_overlap(profile: dict, signals: dict) -> float:
    """Jaccard similarity between student specialites and profession required specialites."""
    return _jaccard(
        set(profile.get("specialites") or []),
        set(signals.get("specialites") or []),
    )
```

Appel dans `score_occupations()` après `f_passion`, `f_valeur`, `f_niveau` :
```python
f_specialite = _specialite_overlap(profile, signals)

raw_contributions = [
    f_passion    * _WEIGHTS["passion_overlap"]      * 100,
    f_valeur     * _WEIGHTS["valeur_alignment"]     * 100,
    f_niveau     * _WEIGHTS["niveau_compatibility"] * 100,
    f_specialite * _WEIGHTS["specialite_overlap"]   * 100,
    f_bulletin   * _WEIGHTS["bulletin_quality"]     * 100,
]
```

Et ajouter le 5ème `SignalContributif` :
```python
SignalContributif(
    signal="specialite_overlap",
    weight=_WEIGHTS["specialite_overlap"],
    contribution=round(raw_contributions[3]),
),
```
(et `niveau_compatibility` contribution devient `raw_contributions[2]`, `bulletin_quality` devient `raw_contributions[4]`)

### 4.5 Post-processing `_reorder_for_level_threshold` — implémentation complète

```python
import math

LEVEL_COMPAT_THRESHOLD = 0.6  # ≥60% of Top 8 must be level-compatible

def _reorder_for_level_threshold(
    sorted_results: list[dict],
    profession_by_id: dict,
    niveau: str,
    threshold: float = LEVEL_COMPAT_THRESHOLD,
) -> tuple[list[dict], bool]:
    """Guarantee ≥threshold of Top 8 are level-compatible when niveau is declared.

    Returns (reordered_top8, was_reordered).
    """
    if not niveau or not sorted_results:
        return sorted_results[:8], False

    target = math.ceil(8 * threshold)  # = 5

    compatible = [
        r for r in sorted_results
        if niveau.lower() in [lc.lower() for lc in (profession_by_id[r["id"]].level_compatibility or [])]
    ]
    incompatible = [r for r in sorted_results if r not in compatible]

    if len(compatible) >= target:
        # Already meets threshold — normal Top 8 (score-ordered)
        return sorted_results[:8], False

    # Boost compatible: take all compatible (sorted by score desc, already the case),
    # then fill remaining slots with highest-scored incompatible.
    reordered = (compatible + incompatible)[:8]
    return reordered, True
```

**Modification de `compute_recommendations()`** — retourner un dict au lieu d'une liste :

```python
def compute_recommendations(user: Any) -> dict[str, Any]:
    # ... existing code unchanged until the merge/sort section ...
    
    scored_occupations.sort(key=lambda x: x.get("score", 0), reverse=True)

    results: list[dict[str, Any]] = []
    for item in scored_occupations:  # iterate ALL, not [:8] — threshold filter takes 8
        occ_id = item.get("occupation_id")
        p = profession_by_id.get(occ_id)
        if p is None:
            continue
        results.append({...})  # same as before

    # --- level threshold post-processing ---
    niveau = profile_dict.get("niveau", "")
    results, niveau_adapted = _reorder_for_level_threshold(results, profession_by_id, niveau)

    return {"results": results, "niveau_adapted": niveau_adapted}
```

**⚠️ IMPORTANT**: `compute_recommendations()` actuellement retourne une `list`. Le changer en `dict` implique de mettre à jour `RecommendationsView` qui aujourd'hui fait :
```python
results = compute_recommendations(request.user)
return Response({"results": results, "computed_at": ...})
```
→ devient :
```python
data = compute_recommendations(request.user)
return Response({"results": data["results"], "computed_at": ..., "niveau_adapted": data["niveau_adapted"]})
```

**⚠️ IMPORTANT** : `test_recommendations.py` mock `compute_recommendations` et vérifie la structure. Mettre à jour les mocks pour retourner un dict au lieu d'une liste.

### 4.6 Frontend — `MetiersList` bandeau

Prop optionnel, pas de breaking change :
```tsx
interface MetiersListProps {
  professions: ScoredProfession[];
  niveauAdapted?: boolean;  // NEW
}

export function MetiersList({ professions, niveauAdapted }: MetiersListProps) {
  // ...
  return (
    <>
      {niveauAdapted && (
        <p
          role="status"
          className="mb-4 rounded-lg bg-blue-50 px-4 py-3 text-sm text-blue-800"
        >
          Tes recos tiennent compte de ton niveau scolaire.
        </p>
      )}
      <ul className="flex flex-col gap-4" data-testid="metiers-list">
        {/* ... existing items ... */}
      </ul>
      {/* ... existing SignauxDrawer ... */}
    </>
  );
}
```

`MesMetiersPage` :
```tsx
export default async function MesMetiersPage() {
  const data = await fetchRecommendations();
  return (
    <main ...>
      <h1 ...>Mes métiers recommandés</h1>
      <Suspense fallback={<MesMetiersLoading />}>
        <MetiersList professions={data.results} niveauAdapted={data.niveau_adapted} />
      </Suspense>
    </main>
  );
}
```

### 4.7 Tests ai-service — structure attendue avec 5 signaux

Mettre à jour `AI_SERVICE_RESPONSE` dans `test_recommendations.py` :
- Ajouter `{"signal": "specialite_overlap", "weight": 0.15, "contribution": 0}` dans chaque `signals_contributifs`
- Changer les contributions `passion_overlap.weight: 0.35 → 0.30`, `valeur_alignment.weight: 0.25 → 0.20`

`test_statistical_scorer.py` :
- `test_score_occupations_*` : vérifier 5 `SignalContributif` par occupation
- Ajouter les tests `_specialite_overlap` (AC6 ai-service)
- Mettre à jour les tests qui assertent la somme des poids (maintenant 5 features)

### 4.8 Note sur l'itération top-8 dans `compute_recommendations()`

Actuellement `for item in scored_occupations[:8]` — couper à 8 AVANT le post-processing priverait le helper de candidats compatibles au-delà du top 8. **Il faut itérer ALL professions scorées, puis appliquer le threshold, puis retourner les 8 finaux.** Le code en 4.5 montre `for item in scored_occupations:` (sans `[:8]`).

### 4.9 Pas de changement au schéma Pydantic ai-service

`ProfessionSignals` a déjà `signals_json: dict = {}` — les spécialités sont dans `signals_json["specialites"]`. Aucun changement de schéma nécessaire côté ai-service.

### 4.10 Leçons des stories précédentes

- **Tests postgresql_only** : le nouveau test Django post-processing n'utilise PAS `ArrayField` directement — il mock `compute_recommendations`, donc peut être `@pytest.mark.django_db` normal (SQLite OK).
- **`compute_recommendations` mock** : `test_recommendations.py` mock déjà `compute_recommendations` avec `@patch`. Mettre à jour le mock value pour retourner un dict.
- **Ruff** : `_WEIGHTS` et `FEATURES` sont des module-level mutables → déjà exemptés via `RUF012` dans `pyproject.toml` (apps/recommendations). L'ai-service utilise `ruff` séparément — vérifier avec `cd apps/ai-service && uv run ruff check src/`.

---

## 5. Dev Agent Record

### Debug Log
_(empty — story not yet started)_

### Completion Notes
_(empty)_

### File List
_(to be filled by dev agent)_

### Change Log
_(to be filled by dev agent)_
