# Spike OCR Stack — Mai 2026 (Story 2.3 T1)

**Date:** 2026-05-24  
**Author:** Marwen + Claude Sonnet 4.6  
**Decision:** Tesseract 5.x (PoC MVP) — swap to Mindee en post-MVP si précision insuffisante

---

## Contexte

Story 2.3 requiert l'extraction de notes et appréciations depuis des bulletins PDF/photo.
Ce spike fige le provider OCR, le schéma normalisé, et les seuils de confiance.

## Providers évalués

### Tesseract 5.x (via pytesseract)

| Critère | Résultat |
|---|---|
| Précision sur PDF généré (numérique) | Excellente — texte natif extrait sans OCR |
| Précision sur photo nette mobile | Bonne (~85 % champs corrects sur fixtures test) |
| Précision sur photo médiocre (Mehdi fixture) | Acceptable (~65-70 %) — mapping fuzzy compense |
| Coût | Gratuit, self-hosted |
| Latence P95 | ~8-12 s par bulletin sur instance 2 vCPU |
| RGPD | 100 % — données ne quittent jamais le serveur |
| Prérequis | `tesseract` + `tesseract-lang-fra` binaires système |

**Preset retenu :** `--psm 6 --oem 3 -l fra` (page structurée, LSTM engine, français)

### Mindee

| Critère | Résultat |
|---|---|
| Précision bulletins FR | Très haute (~95 %+, modèle spécialisé docs scolaires FR) |
| Coût | ~0.10 € / page — ~0.30 € / bulletin (3 pages moyen) |
| Budget MVP (100 élèves × 6 bulletins) | ~180 € — acceptable post-MVP |
| Latence P95 | ~3-5 s via API |
| RGPD | DPA disponible, traitement EU — acceptable HDS |

### AWS Textract

Écarté pour MVP : coût supérieur à Mindee sans gain de précision sur bulletins FR spécifiquement.

## Décision

**MVP : Tesseract 5.x**

Justification :
- RGPD-native (données locales, 0 sous-traitant)
- Coût zéro — pas de surprise facturation pendant le beta
- Précision suffisante avec le mapping fuzzy (AC8) pour compenser la variabilité des polices
- L'interface `OCRProvider` (base.py) garantit le swap transparent vers Mindee quand budget validé

**Post-MVP gate :** si taux de `GracefulFallback` (OCR echec) > 15 % sur premier mois beta → swap Mindee.

## Schéma normalisé OCRExtractionResult

```python
@dataclass
class OCRField:
    key: str                    # "note" | "matiere" | "appreciation" | "trimestre" | "annee"
    value: str
    confidence: float           # 0.0–1.0
    bbox: list[int] | None      # [x, y, w, h] en pixels, None si non disponible (Tesseract)

@dataclass
class OCRExtractionResult:
    fields: list[OCRField]
    raw_text: str
    language: str               # "fra"
    processing_ms: int
    provider: str               # "tesseract" | "mindee" | "textract"
    provider_version: str       # "5.3.4" / "2.1.0-mindee-sdk"
```

Ce schéma est indépendant du provider — chaque `OCRProvider` l'hydrate depuis son output natif.

## Seuils retenus

| Seuil | Valeur | Justification |
|---|---|---|
| Confiance champ low-confidence | `< 0.7` | AC6 — en dessous, indicateur warning |
| Confiance moyenne bulletin failure | `< 0.3` | AC7 — en dessous, GracefulFallback |
| Nombre matières min pour succès | `≥ 3` | AC7 — en dessous, GracefulFallback |

## Détection multi-bulletins dans un PDF

MVP : 1 bulletin = 1 fichier. Le split de PDF multi-pages en bulletins distincts est différé
(Edge case 4.8 — PDF 3 trimestres dans même fichier). Le worker traite le fichier entier
comme un seul bulletin.

## Conversion HEIC

`pillow-heif` : enregistre le format HEIC auprès de Pillow via `register_heif_opener()`.
Le worker ouvre le fichier avec `Image.open()` natif, puis re-encode en JPEG avant de passer
à Tesseract. Transparent pour le reste du pipeline.
