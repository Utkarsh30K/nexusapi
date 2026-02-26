# NexusAPI - Multi-tenant Backend Platform

A production-grade multi-tenant backend platform built with FastAPI, PostgreSQL, and SQLAlchemy.

## Project Structure

```
nexusapi/
├── app/
│   ├── __init__.py
│   ├── config.py           # Configuration management
│   ├── database.py         # Database connection
│   ├── main.py             # FastAPI app entry point
│   ├── models/             # Database models
│   │   ├── base.py
│   │   ├── organisation.py
│   │   ├── user.py
│   │   └── credit.py
│   ├── services/           # Business logic services
│   │   ├── organisation_service.py
│   │   ├── user_service.py
│   │   └── credit_service.py
│   └── routes/             # API routes
├── alembic/                # Database migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── docker/                 # Docker configuration
│   ├── postgres.dockerfile
│   └── postgres.conf
├── tests/                  # Test scripts
│   └── test_multi_tenancy.py
├── .env                   # Environment variables
├── .env.example           # Example env file
├── requirements.txt       # Python dependencies
├── docker-compose.yml     # Docker services
├── create_tables.py       # Script to create tables (legacy)
└── README.md
```

## Prerequisites

- Python 3.12+
- Docker & Docker Compose
- PostgreSQL (via Docker)

## Setup Instructions

### 1. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Or on Linux/Mac
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Start PostgreSQL with Docker

```bash
# Build and start PostgreSQL container
docker-compose up -d postgres

# Check if PostgreSQL is running
docker-compose logs -f postgres

# Stop PostgreSQL when done
docker-compose down
```

### 3. Run Database Migrations (Alembic)

```bash
# Generate initial migration (creates all tables)
alembic revision --autogenerate -m "initial schema"

# Run the migration
alembic upgrade head

# Verify migration history
alembic history
```

### 4. Verify Tables Created

```bash
# Connect to PostgreSQL container
docker exec -it nexusapi_postgres psql -U nexususer -d nexusapi

# List all tables
\dt+

# View table structure
\d users
```

---

## Task 2: Database Migrations with Alembic

### Demo Gate Verification

| Requirement | Verification Command |
|-------------|---------------------|
| `alembic history` shows two migration versions | `alembic history` |
| Users table has new column (avatar_url) | `\d users` in psql |
| Existing rows were not deleted | `SELECT * FROM users;` in psql |

### Adding a New Column (Demo for Task 2)

1. Add the column to the model in `app/models/user.py`:
```python
avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
```

2. Generate a new migration:
```bash
alembic revision --autogenerate -m "add avatar_url to users"
```

3. Run the migration:
```bash
alembic upgrade head
```

4. Verify:
```bash
alembic history
# Should show two migrations
```

### Alembic Commands

```bash
# Generate a new migration
alembic revision --autogenerate -m "migration description"

# Run all pending migrations
alembic upgrade head

# Run a specific migration
alembic upgrade <revision>

# Rollback one migration
alembic downgrade -1

# Rollback all migrations
alembic downgrade base

# Show migration history
alembic history

# Show current revision
alembic current
```

---

## Task 1: Multi-tenancy Test (Previously Created)

Run the multi-tenancy test to verify data isolation:

```bash
# Make sure you're in nexusapi directory with venv activated
cd C:\Users\manoj\Desktop\WORK\Engineering Intern Track\nexusapi
venv\Scripts\activate

# Run the test
python -m tests.test_multi_tenancy
```

---

## Access the API

- API Base URL: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://nexususer:nexuspass@localhost:5432/nexusapi` |
| `DEBUG` | Enable debug mode | `True` |
| `APP_NAME` | Application name | `NexusAPI` |
| `JWT_SECRET_KEY` | Secret key for JWT tokens | `change-me-in-production-use-strong-secret` |
| `JWT_ALGORITHM` | JWT algorithm | `HS256` |
| `JWT_EXPIRATION_MINUTES` | JWT token expiration | `60` |

## Models

### Organisation
- `id` (UUID): Primary key
- `name`: Organisation name
- `domain`: Unique domain (e.g., "acme.com")
- `created_at`: Timestamp
- `updated_at`: Timestamp

### User
- `id` (UUID): Primary key
- `email`: Unique email address
- `name`: User's name
- `organisation_id`: Foreign key to Organisation
- `role`: ADMIN or MEMBER
- `google_id`: Google OAuth ID (nullable)
- `avatar_url`: Profile picture URL (nullable) - **Added in Task 2**
- `created_at`: Timestamp
- `updated_at`: Timestamp

### OrgCredit
- `id` (UUID): Primary key
- `organisation_id`: Foreign key to Organisation (unique)
- `balance`: Credit balance (integer)
- `created_at`: Timestamp
- `updated_at`: Timestamp

### CreditTransaction
- `id` (UUID): Primary key
- `organisation_id`: Foreign key to Organisation
- `amount`: Transaction amount
- `type`: DEDUCTION or REFUND
- `job_id`: Associated job (nullable)
- `description`: Transaction description
- `created_at`: Timestamp
- `updated_at`: Timestamp

## Multi-Tenancy Security

**IMPORTANT**: Every query that touches user data MUST include `organisation_id` as a filter. This is enforced at the database query level, not just in application logic.

Service files include this comment:
```python
"""
SECURITY: All queries MUST include organisation_id filter.
Failure to do so will result in data leakage between tenants.
"""
```

## Tech Stack

- **Backend**: Python 3.12, FastAPI
- **Database**: PostgreSQL, SQLAlchemy (async)
- **ORM**: SQLAlchemy with async support
- **Migrations**: Alembic
- **Auth**: Google OAuth 2.0 + JWT (Tasks 3-4)

## Next Steps

After completing Task 2:
- Task 3: Google OAuth with organisation auto-creation
- Task 4: JWT authentication and role-based middleware
- Assignment 2: Async Job Queue + Background Processing
