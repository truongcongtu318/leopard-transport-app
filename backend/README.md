# LEOPARD Backend

FastAPI backend for the LEOPARD freight transport platform.

## Tech Stack

- **Framework:** FastAPI (async)
- **Database:** PostgreSQL 16 + PostGIS + TimescaleDB
- **ORM:** SQLAlchemy 2.0 (async) + asyncpg
- **Cache / PubSub:** Redis 7
- **Background Jobs:** Celery + Redis broker
- **Auth:** Firebase Admin SDK + JWT
- **AI/ML:** XGBoost (ETA), Google OR-Tools (VRP)
- **External APIs:** Vietmap (routing), OpenWeather

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 16 with PostGIS & TimescaleDB extensions
- Redis 7

### Setup

```bash
# Create virtualenv
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows

# Install dependencies
pip install -r requirements.txt -r requirements-dev.txt

# Copy env config
cp .env.example .env
# Edit .env with your DB/Redis credentials

# Run migrations
alembic upgrade head

# Seed dev data
python -m scripts.seed_data

# Start server
uvicorn app.main:app --reload --port 8000
```

### Docker

```bash
# From project root (where docker-compose.yml is)
docker compose up -d postgres redis
docker compose up backend
```

## Testing

```bash
pytest                    # Run all tests
pytest --cov              # With coverage report
pytest -x -v              # Stop on first failure, verbose
```

## API Docs

Once running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Architecture

```
app/
├── api/          # HTTP/WebSocket boundary (routes)
├── schemas/      # Pydantic request/response models
├── models/       # SQLAlchemy ORM models (17 tables)
├── services/     # Business logic layer
├── repositories/ # Data access layer
├── core/         # Infrastructure (DB, Redis, Firebase, JWT)
└── workers/      # Celery background tasks
```

## License

Private — LEOPARD Project.
