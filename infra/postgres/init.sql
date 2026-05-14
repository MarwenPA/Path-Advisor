-- Path-Advisor — PostgreSQL initialization
-- Runs once on first postgres container boot (mounted at /docker-entrypoint-initdb.d/).
-- Story 1.1 §AC5: enable pgvector + pgcrypto extensions.

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
