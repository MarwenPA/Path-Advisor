## Summary

<!-- 1-3 bullets describing the change and why -->

## Story / Issue

<!-- Link to the story spec, e.g. _bmad-output/implementation-artifacts/1-1-initialisation-projet.md -->

## Acceptance Criteria

<!-- Tick the ACs from the story that this PR satisfies -->

- [ ] AC1
- [ ] AC2
- [ ] ...

## Quality checklist

- [ ] Tests added / updated (unit, integration, or e2e as appropriate)
- [ ] `make lint` clean
- [ ] `make test` green
- [ ] OpenAPI regenerated if the API surface changed (`make openapi`)
- [ ] No business logic in DRF views (services layer used)
- [ ] All user-facing strings go through i18n (`useTranslations` / `gettext`)
- [ ] Sensitive writes wrapped with `@audit_action(...)` when applicable
- [ ] Multi-tenant models include `tenant_id` and respect RLS
- [ ] ADR added under `docs/adr/` if a pattern is deviated from

## Screenshots / videos (UI changes)

<!-- Drop here -->

## Test plan

- [ ] ...
