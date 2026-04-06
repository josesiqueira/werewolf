# Stack Detection — Werewolf AI Agents

## Languages

| Language | Version | Role | Documentation |
|----------|---------|------|---------------|
| Python | 3.12 | Backend API, game engine, agent system | https://docs.python.org/3.12/ |
| TypeScript | 5.x | Frontend UI | https://www.typescriptlang.org/docs/ |
| SQL | PostgreSQL 16 | Data storage | https://www.postgresql.org/docs/16/ |

## Backend Frameworks & Libraries

| Library | Version | Purpose | Documentation |
|---------|---------|---------|---------------|
| FastAPI | 0.115.x | REST API framework | https://fastapi.tiangolo.com/ |
| SQLAlchemy | 2.0.x | ORM / database models | https://docs.sqlalchemy.org/en/20/ |
| Alembic | 1.13.x | Database migrations | https://alembic.sqlalchemy.org/en/latest/ |
| Pydantic | 2.x | Data validation, JSON schemas | https://docs.pydantic.dev/latest/ |
| Uvicorn | 0.30.x | ASGI server | https://www.uvicorn.org/ |
| OpenAI Python SDK | 1.x | GPT 5.4 API calls | https://platform.openai.com/docs/api-reference |
| httpx | 0.27.x | Async HTTP client (OpenAI dependency) | https://www.python-httpx.org/ |
| psycopg2-binary | 2.9.x | PostgreSQL adapter | https://www.psycopg.org/docs/ |
| python-dotenv | 1.x | Environment variable loading | https://pypi.org/project/python-dotenv/ |
| tenacity | 8.x | Retry logic with exponential backoff | https://tenacity.readthedocs.io/ |

## Frontend Frameworks & Libraries

| Library | Version | Purpose | Documentation |
|---------|---------|---------|---------------|
| Next.js | 14.x | React framework (App Router) | https://nextjs.org/docs |
| React | 18.x | UI library | https://react.dev/ |
| Tailwind CSS | 3.4.x | Utility-first CSS | https://tailwindcss.com/docs |
| React Bits | latest | Animated UI components | https://reactbits.dev/ |
| Recharts | 2.x | Chart/visualization library | https://recharts.org/en-US/api |
| D3.js | 7.x | Force-directed graphs (accusation graph) | https://d3js.org/ |
| Zustand | 4.x | Client state management | https://docs.pmnd.rs/zustand |
| TanStack Query | 5.x | Server state / data fetching | https://tanstack.com/query/latest/docs |

## Testing

| Tool | Version | Purpose | Documentation |
|------|---------|---------|---------------|
| pytest | 8.x | Backend unit/integration tests | https://docs.pytest.org/en/stable/ |
| pytest-asyncio | 0.23.x | Async test support for FastAPI | https://pytest-asyncio.readthedocs.io/ |
| pytest-cov | 5.x | Coverage reporting | https://pytest-cov.readthedocs.io/ |
| Vitest | 2.x | Frontend unit/component tests | https://vitest.dev/ |
| Testing Library | 16.x | React component testing | https://testing-library.com/docs/react-testing-library/intro/ |
| Playwright | 1.47.x | End-to-end browser tests | https://playwright.dev/docs/intro |

## Infrastructure

| Tool | Purpose | Documentation |
|------|---------|---------------|
| Docker | Containerization | https://docs.docker.com/ |
| Docker Compose | Local dev orchestration | https://docs.docker.com/compose/ |
| PostgreSQL 16 | Database (CSC Pukki) | https://www.postgresql.org/docs/16/ |
| CSC Rahti (OpenShift) | Production hosting | https://docs.csc.fi/cloud/rahti2/ |

## Commands

### Backend

```bash
# Install dependencies
cd backend && pip install -r requirements.txt

# Run dev server
cd backend && uvicorn app.main:app --reload --port 8000

# Run tests
cd backend && pytest

# Run tests with coverage
cd backend && pytest --cov=app --cov-report=term-missing

# Run database migrations
cd backend && alembic upgrade head

# Create new migration
cd backend && alembic revision --autogenerate -m "description"
```

### Frontend

```bash
# Install dependencies
cd frontend && npm install

# Run dev server
cd frontend && npm run dev

# Build for production
cd frontend && npm run build

# Run unit tests
cd frontend && npx vitest run

# Run unit tests in watch mode
cd frontend && npx vitest
```

### End-to-End Tests

```bash
# Install Playwright browsers
cd frontend && npx playwright install

# Run E2E tests
cd frontend && npx playwright test

# Run E2E tests with UI
cd frontend && npx playwright test --ui
```

### Docker (Full Stack)

```bash
# Start all services
docker compose up -d

# Stop all services
docker compose down

# Rebuild after dependency changes
docker compose up -d --build
```
