# Access-list aggregator pattern

**Story 1.9** introduces the polymorphic access-list aggregator that powers the `/parametres/confidentialite/acces-tiers` page and the `GET /api/v1/profile/access-list/` endpoint. The aggregator unifies third-party access records from heterogeneous sources (today: `parental_consents` ; tomorrow : `school_partnerships`, `counselor_consents`) behind one DTO contract.

## When to add a new source

Add a new `AccessListSource` adapter whenever a story creates a new path for a third party to gain access to a student's profile. Stories 5.4 (école partenaire) and 6.7 (conseillère cohorte) are the next two expected sources.

Adding a source does NOT require :
- changing the API endpoint
- changing the frontend page or components
- writing a new migration (unless your source needs its own table)

## The contract

Implement the `AccessListSource` Protocol from `apps.profiles.access_list.protocols` :

```python
class AccessListSource(Protocol):
    name: str
    def list_for_user(self, user: User) -> list[AccessListEntry]: ...
    def revoke(self, user: User, source_pk: str) -> None: ...
```

Three obligations :

1. **`name`** : a short `[a-z_]+` slug. It becomes the prefix of the composite `id` field of every entry your source produces (`"<name>:<source_pk>"`). Pick something stable — once stories ship that reference it, renaming is a migration.

2. **`list_for_user`** : return a materialized `list[AccessListEntry]`, NOT a Django QuerySet. The aggregator concatenates results across sources of different backends (ORMs, external REST calls, GraphQL) ; only `list` composes safely. Return `[]` on no data — never raise.

3. **`revoke`** : implemented by Story 1.10. Sources written before 1.10 ships can raise `NotImplementedError` ; Story 1.10 will turn this into the active revocation path. The aggregator never calls `revoke` itself — only the revocation endpoint does.

## Wiring the source

Two files :

**`apps/profiles/access_list/sources/<name>.py`** — implement the class.

**`apps/profiles/apps.py::ProfilesConfig.ready()`** — register the instance :

```python
def ready(self) -> None:
    from .access_list import registry
    from .access_list.sources.parental_consent import ParentalConsentSource
    from .access_list.sources.school_partnership import SchoolPartnershipSource  # NEW

    registry.register(ParentalConsentSource())
    registry.register(SchoolPartnershipSource())  # NEW
```

That's it. The aggregator picks it up at startup, the API and the page surface the entries with no further changes.

## The visibility matrix

Every entry your source returns sets `visible_data` + `masked_data` from `apps.profiles.access_list.visibility_matrix.VISIBILITY_MATRIX`. NEVER inline the lists. The matrix is the single source of truth ; changing what a parent sees changes ONE file, not N.

If you add a NEW tier type (e.g., `"counselor"` for Story 6.7), :
1. Add the tier to `TierType` in `dto.py`.
2. Add the entry to `VISIBILITY_MATRIX` in `visibility_matrix.py`.
3. Add the FR label to `ACCESS_LIST_COPY.tierBadge` in `apps/web/src/lib/i18n/fr/access-list.ts`.
4. Add the badge color in `tier-access-card.tsx::TIER_BADGE_CLASSES`.

The cross-check test `test_visibility_matrix.py` will fail loudly if you forget step 2.

## Exception isolation

The aggregator runs each source's `list_for_user` in a `try/except`. A source raising MUST NOT block the others — its exception is logged at ERROR with the source name and the source is silently skipped for that request. This means : if your source's DB goes down, the user sees the OTHER sources' entries without an error UI. The trade-off is intentional ; surfacing per-source errors would clutter the page and confuse non-technical users. Observability catches the outage via the ERROR log + alerting.

## Audit

Reading the access list is itself auditable (NFR-S4). The endpoint writes a single `profile.access_list_read` row per request via `record_audit` (dedup'd via `request._access_list_audit_recorded`). Sources do NOT write their own audit rows for the read path — that would amplify by N per page load.

For revocation (Story 1.10), each source writes a tier-specific audit event (`parental_consent.revoked`, `school_partnership.revoked`, …) on top of the unified `profile.access_revoked` event.

## Performance

§AC8 budget : p95 ≤ 100 ms for 100 entries. Each source's `list_for_user` should run in O(1) DB queries (use `select_related` / `prefetch_related` / `only` aggressively). N+1 across sources is acceptable because `N ≤ 3` for the foreseeable future and the aggregator is invoked once per page load.

The list is capped at 100 entries via `MAX_ENTRIES` in `aggregator.py`. Pagination is deliberately out of scope — a real student has 1–3 entries ; the cap is a 30× safety margin.
