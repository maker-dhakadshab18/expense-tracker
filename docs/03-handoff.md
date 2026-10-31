# Handoff — Personal Expense Tracker (state as of Sat 31 Oct 2026)

Paste this whole file into a new Claude chat to continue. Secrets are NOT included here.

## UPDATE 31 Oct ~18:30 IST: MVP IS LIVE
- Frontend: https://expense-tracker-henna-gamma-48.vercel.app (Vercel, root dir `frontend`, `NEXT_PUBLIC_API_URL` set)
- API: https://expense-tracker-dhakad.el.r.appspot.com (version 20261031t181250); `/health` returns db ok
- Migration 0001 applied to prod `neondb`; `alembic check` is clean; 13/13 pytest pass against `expense_test`
- Live smoke test passed (register, create, summary, delete, CORS preflight from the Vercel origin)
- Fix applied: `alembic.ini` needs `prepend_sys_path = .`
- Prod `backend/env.yaml` exists locally (gitignored). CORS uses `CORS_ORIGIN_REGEX` `^https://expense-tracker[a-z0-9-]*\.vercel\.app$`
- Remaining: manual browser click-through, optional features only.
The sections below describe the state *before* deployment.

## Goal and deadline
MVP personal expense tracker, deployed. **Hard deadline: Sat 31 Oct 2026, 19:00 IST.** ~2 hours left at time of writing.
- Frontend: Next.js on **Vercel**
- API: FastAPI on **Google App Engine Standard**
- DB: **Neon** PostgreSQL (serverless, SSL)

## Environment
- Windows 10, **PowerShell 5.1** (no `&&`; use `;` or `if ($?) { }`)
- Repo root: `C:\Users\HP\PersonalExpenseTrakerProject`, branch `main`, remote `https://github.com/maker-dhakadshab18/expense-tracker`
- Python: **3.11** (3.13 install is broken). Backend venv: `backend\.venv` (deps installed)
- Node 24 / npm 12. No Docker, no local Postgres
- GCP project `expense-tracker-dhakad`, App Engine region `asia-south1`, URL `https://expense-tracker-dhakad.el.r.appspot.com`. APIs enabled: App Engine Admin, Cloud Build. Budget alert set.
- Vercel account linked to GitHub; repo **not yet imported**.

## What is DONE (code written, not yet committed)
### Backend (`backend/`)
- `app/core/config.py`: pydantic-settings reads `.env`. Fields: `DATABASE_URL`, `TEST_DATABASE_URL`, `JWT_SECRET`, `CORS_ORIGINS` (comma-separated), `CORS_ORIGIN_REGEX`. Converts `postgresql://` to `postgresql+psycopg://` automatically.
- `app/core/security.py`: Argon2 via pwdlib, PyJWT HS256, 60-minute tokens.
- `app/db/session.py`: sync SQLAlchemy 2 engine (pool 3+2, `pool_pre_ping`), `Base`, `get_db`.
- `app/models.py`: `users`, `categories` (unique user_id+name), `expenses` (NUMERIC(12,2) CHECK > 0, DATE, note ≤255, index user_id+expense_date).
- `app/schemas.py`: Pydantic contract. Money is a `Decimal` and serialises as a string, e.g. `"250.50"`.
- `app/services.py`: business logic. Every query is scoped to user_id. Another user's expense returns 404; using another user's category returns 422. New users get 8 default categories.
- `app/api.py`: routes (no trailing slashes):
  - `GET /health` (checks the DB)
  - `POST /api/v1/auth/register` → token (201); `POST /api/v1/auth/login` → token; `GET /api/v1/auth/me`
  - `GET/POST /api/v1/categories`
  - `GET /api/v1/expenses?from&to&category_id&page&page_size`; `POST /api/v1/expenses`
  - `GET/PATCH/DELETE /api/v1/expenses/{id}`
  - `GET /api/v1/summary?month=YYYY-MM`
- `app/main.py`: app, CORS middleware, routers.
- `alembic/` + `alembic.ini`: `env.py` uses the app engine; hand-written migration `versions/0001_initial.py`.
- `tests/`: 14 pytest tests (auth, validation, ownership isolation, filters/pagination, summary, health). They use `TEST_DATABASE_URL` and drop/recreate all tables in it.
- `app.yaml`: `runtime: python311`, F1, entrypoint `gunicorn -w 2 -k uvicorn_worker.UvicornWorker -b :$PORT --timeout 60 app.main:app`, `max_instances: 2`, `includes: [env.yaml]`.
- `env.yaml.example`: template. The real `env.yaml` is **gitignored but uploaded** by gcloud and holds prod secrets.
- `.gcloudignore`: excludes .venv, tests, alembic, .env.
- `requirements.txt` (pinned: fastapi 0.162.0, SQLAlchemy 2.1.6, psycopg[binary] 3.3.6, alembic 1.20.1, gunicorn 26.2.0, uvicorn 0.54.0, uvicorn-worker 0.4.0, pydantic 2.14.2, pydantic-settings 2.16.2, pwdlib[argon2] 0.3.1, PyJWT 2.15.1, email-validator 2.3.0), `requirements-dev.txt` (pytest, httpx).
- `.env`: created and gitignored. Contains a generated JWT_SECRET. **The user must paste the Neon URLs into DATABASE_URL and TEST_DATABASE_URL.**

Verified so far: the app imports and all 8 paths appear in OpenAPI. **Nothing has run against a DB yet.**

### Frontend (`frontend/`)
- Next.js 16.4.3, React 19, Tailwind v4, App Router, `src/`. **`npm run build` passes.**
- `src/lib/api.ts`: fetch wrapper. Token is stored in localStorage and sent as a Bearer header. On 401 it clears the token and redirects to /login. FastAPI 422 errors are turned into readable messages. Also exports `formatMoney` (INR) and `todayIST`.
- `src/lib/types.ts`: shared types.
- Pages: `/` (redirect), `/login`, `/register` (shared `components/AuthForm.tsx`), `(app)/layout.tsx` (client-side auth guard + nav + logout), `(app)/expenses` (add form, inline edit, delete confirm, filters, pagination, add category), `(app)/dashboard` (month picker, total, per-category bars).
- `.env.local.example`: `NEXT_PUBLIC_API_URL=http://127.0.0.1:8000`. The value is baked in at build time.

## REMAINING STEPS (in order)
1. User pastes the Neon URLs into `backend/.env`. Two separate databases: `neondb` and `expense_test`.
2. From `backend/`:
   ```powershell
   .venv\Scripts\alembic upgrade head
   .venv\Scripts\alembic check          # should report no differences from the models
   .venv\Scripts\python -m pytest -q
   ```
3. Local smoke test:
   - API: `.venv\Scripts\uvicorn app.main:app --reload` (port 8000), then open `/docs`.
   - Frontend: copy `.env.local.example` to `.env.local`, then `npm run dev` (port 3000).
   - Walk through: register → add → edit → delete → dashboard.
4. `git add -A; git commit`, then `git push` (confirm `.env`/`env.yaml` are NOT staged: `git status`).
5. Create `backend/env.yaml` from the example with the prod DATABASE_URL, a JWT_SECRET (can reuse the one in .env), and `CORS_ORIGINS` = Vercel URL. Then `cd backend; gcloud app deploy`, and check `https://expense-tracker-dhakad.el.r.appspot.com/health` returns `{"status":"ok","db":"ok"}`. Logs: `gcloud app logs tail -s default`.
6. Vercel: import the repo, set **Root Directory = `frontend`**, set env `NEXT_PUBLIC_API_URL=https://expense-tracker-dhakad.el.r.appspot.com`, deploy.
7. Put the Vercel URL into `CORS_ORIGINS` in `env.yaml` (comma-separate with others if needed) and run `gcloud app deploy` again.
8. Test end to end on the live URLs. Update the README with the URLs and setup steps.

## Likely problems
- **Cloud Build permission error on first deploy.** Open the build log link; usually a missing role on the build service account.
- **502 or boot crash.** Check `gcloud app logs tail`. Common causes: missing env var (pydantic-settings raises at import if `DATABASE_URL`/`JWT_SECRET` is missing), or `env.yaml` not uploaded.
- **CORS error in browser.** The origin must exactly match the Vercel URL (https, no trailing slash). Preview URLs can be allowed with `CORS_ORIGIN_REGEX: "https://.*\.vercel\.app"`.
- **Neon cold start.** The first request after idle can be slow; this is acceptable.
- PowerShell `Set-Content -Encoding utf8` writes a BOM. Avoid it for `.env`/yaml files.

## Decisions log
- Bearer JWT in localStorage (cross-site deployment; cookies are unreliable across sites).
- Sync SQLAlchemy + psycopg3. Neon for the DB. Python 3.11 runtime (3.13 install broken).
- Migrations run manually from the laptop against prod before deploy.
- Optional features (charts, budgets, CSV, etc.) only after the MVP is live.
