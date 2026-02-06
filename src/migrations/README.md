# Database Migrations

This directory is reserved for **database migration files** (e.g., Alembic, Django migrations).

## Purpose

This folder is maintained for **alignment with Go SDK structure** and **future use** if database migrations are needed.

## Current Status

- **Status**: Empty (reserved for future use)
- **Current Approach**: SDK uses direct SQL queries with `asyncpg` (no ORM migrations)
- **Database**: PostgreSQL (via asyncpg, not SQLAlchemy ORM)

## Coverage Exclusion

This directory is **excluded from code coverage** calculations:
- Pattern: `**/migrations/**`
- Reason: Migration files are database schema definitions, not business logic
- **Note**: Exclusion pattern is required for alignment with Go SDK coverage standards

## Future Use

If you decide to use database migrations in the future:

### Alembic (SQLAlchemy):
```bash
alembic init migrations
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

### Django:
```bash
python manage.py makemigrations
python manage.py migrate
```

## Notes

- This folder exists primarily for **Go SDK alignment** (coverage exclusion pattern)
- Migration files are automatically excluded from SonarQube coverage
- Keep migration files versioned in Git if added in the future
- Never edit existing migration files after they've been applied to production

---

**Last Updated**: Placeholder for Go SDK alignment and future migration needs

