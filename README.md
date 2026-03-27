# Event Management API

A production-grade REST API built with **Django 4.2 + DRF** for managing events, users, and registrations. Features JWT authentication, role-based permissions, input validation, centralised error handling, Docker support, and a full pytest suite.

---

## Tech Stack

| Layer | Choice |
|---|---|
| Framework | Django 4.2 + Django REST Framework |
| Auth | `djangorestframework-simplejwt` (JWT) |
| Database | PostgreSQL (SQLite fallback for dev) |
| Testing | pytest + pytest-django + Factory Boy |
| Containers | Docker + docker-compose |
| CI | GitHub Actions |

---

## Project Structure

```
event_management_api/
├── core/
│   ├── settings.py          # All config, loaded from .env
│   ├── urls.py              # Root URL routing
│   ├── exceptions.py        # Centralised error handler
│   └── wsgi.py
├── apps/
│   ├── users/
│   │   ├── models.py        # Custom User model (email-first)
│   │   ├── serializers.py   # Registration + login validation
│   │   ├── views.py         # RegisterView, LoginView
│   │   └── urls.py
│   └── events/
│       ├── models.py        # Event, Registration models
│       ├── serializers.py   # Validation + capacity/duplicate checks
│       ├── views.py         # CRUD + registration views
│       ├── permissions.py   # IsOrganizerOrReadOnly
│       └── urls.py
├── tests/
│   ├── factories.py         # Factory Boy factories
│   ├── test_users.py        # User endpoint tests
│   └── test_events.py       # Event endpoint tests
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── pytest.ini
└── .env.example
```

---

## Quick Start (Local — SQLite)

```bash
# 1. Clone and enter project
git clone https://github.com/FredrickMbithi/event_management_api
cd event_management_api

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env — set DJANGO_SECRET_KEY at minimum
# Leave DATABASE_URL commented out to use SQLite

# 5. Run migrations
python manage.py migrate

# 6. Start server
python manage.py runserver
# API available at http://127.0.0.1:8000
```

---

## Quick Start (Docker + PostgreSQL)

```bash
cp .env.example .env
# Edit .env — set DJANGO_SECRET_KEY

docker-compose up --build
# API available at http://localhost:8000
```

---

## Running Tests

```bash
pytest                          # all tests + coverage report
pytest tests/test_users.py      # users only
pytest tests/test_events.py     # events only
pytest -k "test_register"       # filter by name
```

---

## API Reference

### Authentication

All protected routes require:
```
Authorization: Bearer <access_token>
```

---

### Users

#### `POST /users/register/`
Create a new user account.

**Request body:**
```json
{
  "name": "Ghost",
  "email": "ghost@example.com",
  "password": "secure123"
}
```

**Response `201`:**
```json
{
  "user": { "id": 1, "name": "Ghost", "email": "ghost@example.com", "created_at": "..." },
  "tokens": { "access": "...", "refresh": "..." }
}
```

**Validation rules:**
- `email` — valid format, unique
- `password` — minimum 6 characters (never returned in response)
- `name` — non-empty

---

#### `POST /users/login/`
Authenticate and receive JWT tokens.

**Request body:**
```json
{
  "email": "ghost@example.com",
  "password": "secure123"
}
```

**Response `200`:**
```json
{
  "user": { "id": 1, "name": "Ghost", "email": "ghost@example.com" },
  "tokens": { "access": "...", "refresh": "..." }
}
```

---

#### `POST /token/refresh/`
Get a new access token using a refresh token.

**Request body:**
```json
{ "refresh": "<refresh_token>" }
```

---

### Events

#### `GET /events/` — Public
Returns all events with organizer details and live registration count.

**Response `200`:**
```json
[
  {
    "id": 1,
    "title": "Tech Talk Nairobi",
    "description": "...",
    "location": "iHub, Nairobi",
    "date": "2026-05-01T14:00:00Z",
    "max_attendees": 50,
    "organizer": { "id": 1, "name": "Ghost", "email": "ghost@example.com" },
    "registration_count": 12,
    "is_full": false,
    "created_at": "...",
    "updated_at": "..."
  }
]
```

---

#### `POST /events/` — 🔒 Auth required
Create a new event. Organizer is set automatically from JWT token.

**Request body:**
```json
{
  "title": "Tech Talk Nairobi",
  "description": "Annual developer meetup",
  "location": "iHub, Nairobi",
  "date": "2026-05-01T14:00:00Z",
  "max_attendees": 50
}
```

**Validation rules:**
- `title` — required, non-empty
- `date` — must be in the future
- `max_attendees` — optional; if provided, must be ≥ 1

---

#### `PUT /events/:id/` — 🔒 Organizer only
Full update of an event. Returns `403` if caller is not the organizer.

#### `PATCH /events/:id/` — 🔒 Organizer only
Partial update (bonus endpoint).

#### `DELETE /events/:id/` — 🔒 Organizer only
Delete an event. Returns `403` if caller is not the organizer.

---

#### `POST /events/:id/register/` — 🔒 Auth required
Register the authenticated user for an event.

**Response `201`:**
```json
{
  "message": "Successfully registered for 'Tech Talk Nairobi'.",
  "registration": {
    "id": 5,
    "user": { "id": 2, "name": "Jeff", "email": "jeff@example.com" },
    "event_id": 1,
    "event_title": "Tech Talk Nairobi",
    "registered_at": "..."
  }
}
```

**Error cases:**
- `400` — already registered for this event
- `400` — event is at full capacity
- `404` — event not found

---

## Error Response Format

All errors return a consistent JSON envelope:

```json
{
  "error": "Human-readable summary",
  "details": { "field": ["specific validation message"] }
}
```

| Status | Meaning |
|---|---|
| `400` | Bad input / validation failure |
| `401` | Missing or invalid JWT token |
| `403` | Authenticated but not authorised (wrong organizer) |
| `404` | Resource not found |

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `DJANGO_SECRET_KEY` | Yes | Django secret key |
| `DEBUG` | No | `True` for dev, `False` for prod |
| `ALLOWED_HOSTS` | No | Comma-separated hostnames |
| `DATABASE_URL` | No | PostgreSQL URL; omit for SQLite |

---

## Deployment (Render / Railway)

1. Set all environment variables in the platform dashboard
2. Set `DEBUG=False` and `ALLOWED_HOSTS=your-domain.com`
3. Add a build command: `pip install -r requirements.txt && python manage.py migrate`
4. Start command: `gunicorn core.wsgi:application --bind 0.0.0.0:$PORT`
5. Add `gunicorn` to `requirements.txt`

---

## Design Decisions

**Custom User model** — Always extend `AbstractBaseUser` from day one. Migrating the user model mid-project is painful; starting clean costs nothing.

**Email as USERNAME_FIELD** — More natural for end users than a username; enforced unique at DB level.

**Centralised exception handler** — Single place (`core/exceptions.py`) controls every error response shape. Adding Sentry integration later is one line here.

**DB-level + serializer-level duplicate guard** — The serializer gives a clean 400 with a readable message; the `unique_together` constraint is the last-resort safety net if two concurrent requests slip through.

**IsOrganizerOrReadOnly permission** — Composable object-level permission; if you later add admin roles, you extend this class rather than scattering `if` checks across views.

**Factory Boy over fixtures** — Factories are code, so they're refactorable. Django fixtures go stale silently.
