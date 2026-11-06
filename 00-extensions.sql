-- Se ejecuta solo en la primera creación del volumen de Postgres (docker-entrypoint-initdb.d).
-- Alembic (0001_baseline) también las crea con IF NOT EXISTS, para entornos gestionados (Railway/Render).
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
