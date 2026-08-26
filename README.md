# RazorGrowth AI

**AI-native Agentic Commerce Platform** — helps merchants grow revenue and become transactable by AI buyers.

## Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Node.js 22+ (for frontend, not yet implemented)

### 1. Start infrastructure

```bash
docker compose up -d
```

This starts PostgreSQL 17 (port 5432) and Redis 7 (port 6379).

### 2. Create virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r apps/api/requirements.txt
pip install -e ".[dev]"
```

### 4. Configure environment

```bash
cp .env.example .env
# Edit .env with your settings (defaults work for local Docker)
```

### 5. Run migrations

```bash
alembic upgrade head
```

### 6. Start the API

```bash
cd apps/api
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 7. Verify

```bash
curl http://localhost:8000/api/v1/health
```

## Project Structure

```
razorgrowth-ai/
├── apps/
│   ├── api/          # FastAPI backend
│   └── web/          # Next.js frontend (planned)
├── migrations/       # Alembic database migrations
├── tests/            # Unit, integration, and e2e tests
├── infrastructure/   # Docker and deployment configs
├── packages/         # Shared packages
└── docs/             # Project documentation
```

## Architecture

- **Backend:** FastAPI + SQLAlchemy async + PostgreSQL
- **Cache:** Redis
- **Migrations:** Alembic
- **Auth:** JWT + bcrypt
- **Containers:** Docker Compose

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Running Tests

```bash
pytest
pytest --cov=app tests/
```

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python) |
| Frontend | Next.js (TypeScript) — planned |
| Database | PostgreSQL 17 |
| ORM | SQLAlchemy 2.x (async) |
| Migrations | Alembic |
| Cache | Redis 7 |
| Auth | JWT + bcrypt |
| Containers | Docker Compose |
