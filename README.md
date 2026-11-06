# NutriAI

Planes de alimentación personalizados con IA y doble motor nutricional
(**SMAE** mexicano + **USDA FoodData Central**), para usuarios finales y nutricionistas.

> Esta app no sustituye la consulta con un profesional de la salud.

## Arranque rápido (Docker)

Requisitos: Docker 24+ con Compose v2.24+.

```bash
git clone <repo-url> nutriai && cd nutriai
cp .env.example .env
docker compose up --build
```

| Servicio | URL |
|---|---|
| Frontend | http://localhost:3000 |
| API (liveness) | http://localhost:8000/api/health |
| API (readiness: Postgres + Redis) | http://localhost:8000/api/health/ready |
| OpenAPI / Swagger | http://localhost:8000/api/docs |

El backend aplica `alembic upgrade head` al arrancar.

## Tests

```bash
make test-backend     # pytest + cobertura (dentro del contenedor)
make test-frontend    # Vitest
make e2e              # Playwright contra el stack levantado (requiere `npm install` en frontend/)
make lint             # ruff + mypy + eslint + tsc
```

Sin Docker:

```bash
# Backend (Python 3.11+)
cd backend && python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]" && pytest --cov=app

# Frontend (Node 20+)
cd frontend && npm install && npm test
```

## Estructura del monorepo

Los elementos marcados con `(Mn)` se crean en el módulo *n*; el resto existe desde el Módulo 1.

```
nutriai/
├── .github/workflows/ci.yml        # lint, tipos, migraciones, tests, build, E2E
├── docker-compose.yml              # db (PG15) + redis (7) + backend + frontend
├── .env.example
├── Makefile
├── README.md · LICENSES.md
├── ARCHITECTURE.md (M11) · API.md (M11, autogenerado desde OpenAPI)
├── infra/
│   ├── postgres/init/00-extensions.sql
│   └── deploy/ (M11)               # railway.json, render.yaml, vercel.json
├── backend/
│   ├── Dockerfile · pyproject.toml · alembic.ini
│   ├── alembic/
│   │   ├── env.py                  # async, URL desde DATABASE_URL
│   │   └── versions/
│   │       └── 20261105_0001_baseline.py   # pgcrypto + pg_trgm
│   ├── app/
│   │   ├── main.py                 # create_app(), CORS, middleware, handlers
│   │   ├── core/
│   │   │   ├── config.py           # Settings (pydantic-settings) + validación prod
│   │   │   ├── exceptions.py       # AppError + handlers → envelope estándar
│   │   │   ├── responses.py        # ApiResponse[T] {success, data, error}
│   │   │   ├── middleware.py       # X-Request-ID + Server-Timing + log
│   │   │   ├── logging.py · redis.py
│   │   │   └── security.py (M2)    # JWT, hashing, cifrado de columnas
│   │   ├── db/ base.py · session.py
│   │   ├── models/ (M2+)           # user, profile, smae_food, meal_plan, ...
│   │   ├── schemas/ (M2+)          # Pydantic v2 request/response
│   │   ├── api/
│   │   │   ├── router.py
│   │   │   └── routes/
│   │   │       ├── health.py
│   │   │       ├── auth.py · profile.py (M2)
│   │   │       ├── foods.py (M4-M5) · plans.py (M6) · tracking.py · feedback.py (M8)
│   │   │       ├── nutritionist.py (M9) · coach.py · export.py (M10)
│   │   ├── services/
│   │   │   ├── nutrition_engine.py (M3)
│   │   │   ├── smae_module/ (M4)
│   │   │   ├── usda_client/ (M5)
│   │   │   ├── optimizer/ (M6)
│   │   │   └── llm_layer/ (M7)     # prompts.py, clientes OpenAI/Groq, validación
│   │   └── workers/ (M7)           # cola de tareas IA en Redis
│   ├── scripts/ seed_smae.py (M4)
│   └── tests/
│       ├── conftest.py · test_health.py · test_exceptions.py · test_config.py
└── frontend/
    ├── Dockerfile · package.json · tsconfig.json · next.config.mjs
    ├── tailwind.config.ts · components.json (shadcn/ui)
    ├── vitest.config.ts · playwright.config.ts
    ├── e2e/home.spec.ts
    └── src/
        ├── app/
        │   ├── layout.tsx · page.tsx · providers.tsx (React Query) · globals.css
        │   ├── (auth)/login · register (M2/M8)
        │   ├── (app)/dashboard/{onboarding,plan,tracking,progress,coach} (M8, M10)
        │   └── (pro)/nutritionist/{patients,patients/[id],plans/review,messages} (M9)
        ├── components/ui/ (shadcn, M8)
        ├── stores/ (Zustand, M8)
        └── lib/ api.ts · api.test.ts · utils.ts
```

## Convenciones de la API

- Todas las respuestas: `{ "success": bool, "data"?: T, "error"?: { "code", "message", "details"? } }`.
- Errores centralizados en `backend/app/core/exceptions.py` (`NotFoundError`, `BusinessRuleError`,
  `RateLimitError`, …). Los errores 500 nunca exponen detalles internos.
- Cada respuesta incluye `X-Request-ID` y `Server-Timing`.
- En `ENVIRONMENT=production` el backend **no arranca** si `JWT_SECRET_KEY` es débil,
  falta `FIELD_ENCRYPTION_KEY`, `DEBUG=true` o `CORS_ORIGINS=*`.

## Migraciones

```bash
make migrate                         # alembic upgrade head
make revision m="crear tabla users"  # autogenerar nueva migración
```

## Licencias

Ver [LICENSES.md](LICENSES.md). Datos USDA: "FoodData Central, USDA" (CC0).
SMAE: uso educativo con atribución; uso comercial requiere licencia del editor.
