# Referential Sources — Story 3.2

## Overview

This document describes the sources used to curate the 52 MVP professions in `professions_seed`, the extraction dates, and the selection methodology.

---

## Sources Used

| Source | Type | Extraction date | Used for |
|---|---|---|---|
| **Onisep** (onisep.fr/métiers) | Open data, public reference | June 2026 | Descriptions, daily routines, salary ranges, requirements |
| **ROME v4.0** (France Travail / Pôle Emploi) | Occupational taxonomy | June 2026 | `rome_code`, skills categories, job titles |
| **Apec** (apec.fr) | Salary surveys 2025 | June 2026 | Salary ranges for Bac+5 professions |
| **France Travail** (francetravail.fr) | Employment surveys 2025 | June 2026 | Salary ranges for accessible jobs (CAP/Bac Pro) |
| **Validation humaine 2026-06** | Internal editorial review | June 2026 | Ethical curation checklist, content quality review |

---

## Selection Methodology

### Goals

1. **Reach 50+ professions** to feed the scoring engine (Story 3.3) with a credible foundation.
2. **Represent all levels**, from 3ème/CAP through postbac, to avoid "grandes écoles" bias.
3. **Mehdi profile** (bac pro / voies techniques): at least 30% of professions accessible via `lycee_1ere_tle_pro` or `college_3eme`. This is a non-negotiable equity requirement.
4. **Sector diversity**: at least 9 distinct sector families, none dominating excessively.

### Selection Process

1. Extracted candidate professions from Onisep "Métiers" database, filtered by:
   - French labour market relevance (volume of job offers on France Travail ≥ 5,000/year)
   - Availability of structured data (description, salary, training pathway)

2. Enriched with ROME v4.0 codes for cross-referencing with job offers in Story 3.3.

3. Applied ethical curation checklist (see `curation-guide.md`):
   - Verified minimum 30% bac-pro compatible
   - Verified minimum 30% college_3ème compatible
   - Reviewed for gender stereotypes in descriptions and daily routines
   - Ensured bac-pro professions span ≥5 different sectors

4. **All final content was reviewed by a human editor** before merge, per `"validation humaine 2026-06"` source tag.

### Limitations

- 52 professions is the strict MVP count. Scale to 500 is covered by NFR-SC5.
- Salary data from Onisep and Apec may have a 1-year lag vs current market.
- Descriptions are simplified for 15–18 year olds and are not exhaustive professional definitions.
- Automatic import from Onisep API is deferred to V2 (Story 3.2 deferred items).
