# Onboarding Step 3 — Bulletin Import (OCR)

Story 2.3. Lets students import their school reports via photo/scan, with automatic OCR extraction and a manual validation step.

## Flow

```
idle → picking_files → uploading → ocr_running → recap_editing → validated
                                               ↘ fallback (OCR fail)
```

### State machine

`onboarding-step3-machine.ts` — XState v5. States:

| State | What the user sees |
|---|---|
| `idle` | 3-card choice (scan / manual / later) |
| `picking_files` | FilePickerSheet (photo + file picker) |
| `uploading` | UploadProgress with per-file bars |
| `ocr_running` | OCRLoader wrapping `<ScenarioLoader>` |
| `recap_editing` | BulletinRecapEditor (editable table per bulletin) |
| `fallback` | OCRGracefulFallback (2 equivalent CTAs) |
| `validated` | Redirect to dashboard |

## Backend

### Upload `POST /api/v1/students/me/bulletins/upload`

- Accepts: `application/pdf`, `image/jpeg`, `image/png`, `image/heic`
- Max: 10 MB per file, 6 bulletins per student
- S3 key pattern: `bulletins/{student_id}/{uuid}.{ext}`
- Returns `{ bulletin_id, file_path }`

### OCR `POST /api/v1/students/me/bulletins/ocr/start`

- Body: `{ bulletin_ids: string[] }`
- Dispatches Celery `ocr_extract` task per bulletin
- Returns `{ job_ids, estimated_seconds }`

### Status `GET /api/v1/students/me/bulletins/ocr/status?bulletin_id=...`

- Poll until `status` ∈ `{succeeded, failed, timeout}`
- `extraction.is_low_quality = true` → send to fallback state
- `confidence_avg < 0.7` on individual fields → `isLowConfidence: true`

### Finalize `PATCH /api/v1/students/me/bulletins/{id}/finalize`

- Body: `{ fields: NormalizedField[] }`
- Commits student corrections, sets `validated_at`

## OCR Provider

Abstract base: `apps/api/apps/bulletins/providers/base.py`  
MVP: `TesseractProvider` (`--psm 6 --oem 3 -l fra`)  
Post-MVP: swap to Mindee if error rate > 15% (spike: `docs/spikes/ocr-stack-2026-05.md`)

### Quality thresholds

| Condition | Outcome |
|---|---|
| `confidence_avg >= 0.7` | Normal recap, no warnings |
| `field.confidence < 0.7` | Warning indicator on the field |
| `confidence_avg < 0.3` OR `< 3 matières` | `is_low_quality = true` → fallback |

## Subject mapping

`fuzzy_subject_mapper.py` — Levenshtein distance < 3 against canonical referential.  
NFKD unicode normalization before comparison.  
Unknown subjects → `unmapped: true` in the recap (user can type the name manually).

## GDPR / Purge

- `expires_at = uploaded_at + 30 days` set on every bulletin at upload
- `purge_expired_bulletins` Celery beat task (daily): deletes DB rows + S3 objects where `expires_at < now() AND validated_at IS NULL`

## Draft persistence

LocalStorage key: `bulletins_recap_draft_{bulletin_id}`  
Written on every field edit (debounced in component).  
Cleared on finalize.  
Loaded on OCR success to restore any prior edits.

## Analytics events

| Event | When |
|---|---|
| `onboarding_step3_card_selected` | Card click |
| `onboarding_step3_upload_started` | Upload begins |
| `onboarding_step3_upload_completed` | All uploads done |
| `onboarding_step3_ocr_manual_fallback` | User picks manual from fallback |
| `onboarding_step3_bulletin_finalized` | One bulletin validated |
| `onboarding_step3_completed` | All bulletins validated |

## Dependencies added

- Backend: `pytesseract>=0.3`, `pillow-heif>=0.18`, `python-Levenshtein>=0.25`
- Frontend: `xstate@^5`, `@xstate/react@^5`
- System: `tesseract-ocr` + `tesseract-ocr-fra` language pack (installed in Docker image)
