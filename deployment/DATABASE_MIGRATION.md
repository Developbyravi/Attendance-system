# SmartAttend — Database Migration Guide (SQLite to PostgreSQL / Supabase)

## 1. Overview

SmartAttend Backend2 is built with SQLAlchemy 2.0 and supports both:
- **Local Development**: SQLite (`sqlite:///./smartattend.db`)
- **Production**: PostgreSQL (`postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres`)

The application automatically detects the database dialect from `DATABASE_URL` and initializes tables and constraints dynamically upon startup.

---

## 2. Zero-Downtime Migration Steps

### Step 1: Provision Supabase / RDS Database
1. In Supabase Dashboard, create a new project or obtain your connection pooler URI:
   ```text
   postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
   ```
2. Or use direct PostgreSQL connection on port `5432`.

### Step 2: Auto-Generate Schema
Set `DATABASE_URL` in your production environment (`deployment/.env`). When FastAPI starts:
- `Base.metadata.create_all(bind=engine)` creates all 11 tables with proper indices and unique constraints.
- Seeds default institutional administrator (`admin@smartattend.edu`).

### Step 3: Data Migration Script (SQLite $\to$ PostgreSQL)
If you wish to copy local SQLite student records and face embeddings to PostgreSQL:

```bash
# Run migration script
python backend2/scripts/migrate_sqlite_to_postgres.py --sqlite-db backend2/smartattend.db --postgres-url "postgresql://..."
```

---

## 3. Database Integrity & Constraints Checklist
- `(lecture_session_id, student_id)` unique constraint on `lecture_attendances`.
- `(student_id, date)` unique constraint on `daily_checkins`.
- Foreign key constraints with `ON DELETE CASCADE` enabled.
