# Personal Expense Tracker

Track personal expenses by category and see a monthly summary.

- **App:** https://expense-tracker-henna-gamma-48.vercel.app
- **API:** https://expense-tracker-dhakad.el.r.appspot.com (interactive docs at [`/docs`](https://expense-tracker-dhakad.el.r.appspot.com/docs))

> The first request after a period of inactivity can take a few seconds (App Engine and Neon both scale to zero).

## Features
- Register / log in / log out (email + password, Argon2 hashing, JWT bearer tokens)
- Add, edit, delete expenses (amount, date, category, optional note)
- Default categories for every new user, plus your own custom categories
- Filter by date range and category; paginated, newest first
- Monthly summary: total and per-category breakdown
- Validation on both client and server; every query is scoped to the logged-in user

## Stack
| Layer | Tech | Hosted on |
|---|---|---|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS 4 | Vercel |
| API | FastAPI, SQLAlchemy 2 (sync), Pydantic 2, Alembic | Google App Engine Standard (Python 3.11) |
| Database | PostgreSQL | Neon |

Money is stored as `NUMERIC(12,2)` and handled as `Decimal`. The API returns amounts as strings (e.g. `"250.50"`) so there is never any float rounding.

## Project layout
```
backend/    FastAPI app (app/), Alembic migrations, pytest suite, App Engine config
frontend/   Next.js app (src/app routes, src/components, src/lib/api.ts)
docs/       Requirements, architecture, progress notes
```

## API
| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness + DB check |
| POST | `/api/v1/auth/register` | Create account, returns token |
| POST | `/api/v1/auth/login` | Returns token |
| GET | `/api/v1/auth/me` | Current user |
| GET / POST | `/api/v1/categories` | List / create |
| GET / POST | `/api/v1/expenses` | List (`from`, `to`, `category_id`, `page`, `page_size`) / create |
| GET / PATCH / DELETE | `/api/v1/expenses/{id}` | Read / update / delete (404 if not yours) |
| GET | `/api/v1/summary?month=YYYY-MM` | Monthly totals |

## Running locally (Windows / PowerShell)

Prerequisites: Python 3.11, Node.js 20.9+, a PostgreSQL database (e.g. a free Neon project) with two databases: one for the app and a separate one for tests.

### Backend
```powershell
cd backend
py -3.11 -m venv .venv
.venv\Scripts\pip install -r requirements-dev.txt
Copy-Item .env.example .env        # then fill in DATABASE_URL, TEST_DATABASE_URL, JWT_SECRET
.venv\Scripts\alembic upgrade head
.venv\Scripts\uvicorn app.main:app --reload   # http://127.0.0.1:8000/docs
```

Run tests. They use `TEST_DATABASE_URL` and wipe that database:
```powershell
.venv\Scripts\python -m pytest -q
```

### Frontend
```powershell
cd frontend
npm install
Copy-Item .env.local.example .env.local   # NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
npm run dev                                # http://localhost:3000
```

## Deployment

### Database migrations
App Engine has no release hook, so run migrations from your machine **before** deploying code that needs them:
```powershell
cd backend; .venv\Scripts\alembic upgrade head
```

### API → App Engine
1. Create `backend/env.yaml` from `env.yaml.example`. It is gitignored but uploaded by gcloud, and `app.yaml` pulls it in via `includes:`.
   - `DATABASE_URL`: the prod Neon URL
   - `JWT_SECRET`: a long random string
   - `CORS_ORIGINS`: comma-separated exact origins
   - `CORS_ORIGIN_REGEX`: optional; currently allows `https://expense-tracker*.vercel.app`
2. `cd backend; gcloud app deploy`
3. Check `/health`, and tail the logs with `gcloud app logs tail -s default`.

### Frontend → Vercel
Import the GitHub repo with **Root Directory = `frontend`** and set `NEXT_PUBLIC_API_URL` to the API URL. The value is baked in at build time, so changing it requires a redeploy. Every push to `main` deploys to production automatically.

## Known limitations / next steps
- JWT is kept in `localStorage` (simple for a cross-site frontend/API; readable by XSS). Upgrade path: same-origin proxy + httpOnly cookie.
- No refresh tokens: sessions expire after 60 minutes.
- Single currency (INR). No editing or deleting of categories.
- Optional features not yet built: charts, budgets, CSV export, search, recurring expenses, password reset, CI.
