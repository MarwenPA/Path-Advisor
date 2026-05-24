"""Test settings for the PostgreSQL CI lane (Story 1.8 T7).

Story 1.8 enables Row-Level Security, which SQLite cannot exercise. This
settings file targets a real Postgres instance (the `postgres` service in
`docker-compose.yml` or the `services: postgres:16` CI container) so:

- the `@pytest.mark.postgresql_only` suite (audit trigger immutability,
  GDPR archival, Story 1.8 RLS tests) actually runs;
- `FORCE ROW LEVEL SECURITY` actually bites — which requires the test DB
  role to be `NOSUPERUSER NOBYPASSRLS` (cf. story §6 #1). The role +
  database provisioning runs as a separate init step in the CI workflow
  before pytest starts.

The SQLite fast path (`path_advisor.settings.test`) keeps owning the ~95 %
of tests that have no RLS dependency, so local development stays fast.
"""

from __future__ import annotations

import os

from .test import *  # noqa: F403  — inherits SECRET_KEY, EMAIL_BACKEND, etc.

# Real PostgreSQL: the CI workflow boots a `postgres:16` service container
# (or developers can point at the docker-compose `postgres` service locally).
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "path_advisor_test"),
        "USER": os.environ.get("POSTGRES_USER", "path_advisor_test"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "ci_test_role"),
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
        # The autouse fixture in `apps/api/conftest.py` issues `RESET ALL`
        # between tests; keep CONN_MAX_AGE off in tests so connection reuse
        # does not muddle that contract.
        "CONN_MAX_AGE": 0,
    },
}
