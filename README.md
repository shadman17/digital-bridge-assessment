# Digital Bridge Assessment

A Django REST API that connects to an external booking system, synchronizes providers/customers/services/appointments into a local PostgreSQL database, and exposes query/reporting endpoints.

## Tech Stack
- Python 3.12
- Django 4.2 + Django REST Framework
- PostgreSQL
- Celery + Redis (background sync + scheduler)
- Docker / Docker Compose

## Project Structure
- `project_appointment/`: Django project settings, URL routing, Celery app.
- `app_core/`: shared utilities (timestamp model, HTTP client for booking system, management commands).
- `app_booking/`: domain models, sync logic, API views, serializers, pagination, tasks, and management commands.

## Setup Instructions

### 1) Clone and enter project
```bash
git clone https://github.com/shadman17/digital-bridge-assessment.git
cd digital-bridge-assessment
```

### 2) Create environment file
Create a `.env` in the project root:

```env
SECRET_KEY=dev-secret
DEBUG=1
ALLOWED_HOSTS=127.0.0.1,localhost
BASE_URL=http://localhost:8000/

DB_NAME=appointment_db
DB_USER=appointment_user
DB_PASSWORD=appointment_pass
DB_HOST=db
DB_PORT=5432

CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

### 3) Build and start services
```bash
docker compose up --build
```

This starts:
- `web` (Django API on `:8000`)
- `db` (PostgreSQL)
- `redis`
- `celery_worker`
- `celery_beat` (periodic sync every 6 hours)
- `flower` (Celery dashboard on `:5555`)

### 4) Apply migrations (if not already applied during startup)
```bash
docker compose exec web python manage.py migrate
```

### 5) Create a superuser to for admin dashboard
```bash
docker compose exec web python manage.py createsuperuser
```

## How to Run (without Docker)

1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Ensure PostgreSQL + Redis are running and `.env` has localhost values.
4. Run migrations:
   ```bash
   python manage.py migrate
   ```
5. Start Django:
   ```bash
   python manage.py runserver
   ```
6. In separate terminals, start Celery worker and beat:
   ```bash
   celery -A project_appointment worker -l info
   celery -A project_appointment beat -l info
   ```

## API Overview
Base path: `/api/`

- `POST /booking-systems/connect/` — register and validate a booking system.
- `GET /booking-systems/<id>/status/` — sync status + local record counts.
- `GET /booking-systems/<id>/providers/` — paginated providers (`search` supported).
- `GET /booking-systems/<id>/customers/` — paginated customers (`search` supported).
- `GET /booking-systems/<id>/services/` — paginated services.
- `GET /booking-systems/<id>/appointments/` — paginated appointments (`start_date`, `end_date`).
- `POST /booking-systems/<id>/sync/` — enqueue async sync task.
- `GET /booking-systems/<id>/sync/status/` — sync progress/error details.

## Useful Commands

### Seed local data
```bash
python manage.py seed_booking_data --booking_system_id <id>
```

### Generate analytics report
```bash
python manage.py generate_report --booking_system_id <id> --start_date YYYY-MM-DD --end_date YYYY-MM-DD
```

## Design Decisions

1. **Asynchronous synchronization with Celery**  
   Sync is triggered via API and executed in background workers to avoid blocking request/response flow for large imports.

2. **Deterministic sync order** (`providers -> customers -> services -> appointments`)  
   Appointments depend on existing related entities, so parent records are imported first.

3. **Idempotent upserts using `update_or_create`**  
   Re-running sync updates existing rows instead of duplicating data.

4. **Uniqueness scoped by booking system + external ID**  
   Each domain model enforces unique constraints per source system to safely support multiple connected systems.

5. **Resilient external client**  
   The booking system client uses retries, timeout handling, pagination support, and status-specific behavior (e.g., 429 backoff).

6. **Envelope-based API responses + pagination metadata**  
   Responses follow a consistent `{data, errors, meta}` structure to simplify API consumers.

7. **Periodic sync via Celery Beat**  
   A scheduled task keeps connected systems fresh automatically every 6 hours, reducing manual intervention.

## Notes
- Flower UI is exposed at `http://localhost:5555` for task monitoring.
- Default admin URL: `http://localhost:8000/admin/`.