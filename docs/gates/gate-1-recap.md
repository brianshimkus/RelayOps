# Gate 1 recap: first vertical slice

**Goal:** prove a real, boring, no-AI path works end to end:
browser → Next.js → FastAPI → PostgreSQL → back to the browser — and that
the data actually persists in the database, not just in a process's memory.

No AI is allowed to touch this gate. The whole point is to have a
trustworthy, testable foundation *before* adding anything probabilistic.

---

## 1. The architecture, in one picture

```
┌─────────────┐      fetch()       ┌─────────────┐      SQL       ┌──────────────┐
│  Browser    │ ─────────────────► │  Next.js    │ ──────────────►│  FastAPI     │
│ (port 3000) │ ◄───────────────── │ (server     │ ◄───────────── │ (port 8000)  │
└─────────────┘     rendered HTML  │  component) │   JSON         └──────┬───────┘
                                    └─────────────┘                       │ SQLModel /
                                                                          │ SQLAlchemy
                                                                          ▼
                                                                   ┌──────────────┐
                                                                   │  PostgreSQL  │
                                                                   │ (Docker,     │
                                                                   │  port 5433)  │
                                                                   └──────────────┘
```

Key idea: the Next.js page (`web/src/app/page.tsx`) is a **React Server
Component** — it's `async`, and it calls `listIncidents()` *on the server*,
before any HTML reaches your browser. There's no client-side spinner for
this simple case; the page arrives already populated.

---

## 2. What lives where

| Path | What it's for |
|---|---|
| `compose.yaml` | Runs Postgres (with `pgvector`) in Docker on port `5433` |
| `api/app/config.py` | Loads settings (DB URL, ports, etc.) from `.env` via `pydantic-settings` |
| `api/app/database.py` | Creates the SQLAlchemy engine + a `get_session()` dependency for FastAPI |
| `api/app/models.py` | `SQLModel` table classes — these ARE the database schema, in Python |
| `api/app/schemas.py` | Pydantic request/response shapes (what the API accepts/returns — separate from the DB models on purpose) |
| `api/app/routers/incidents.py` | The actual HTTP endpoints: create/list/get incidents |
| `api/app/main.py` | Wires the FastAPI app together (CORS, routers, `/health`) |
| `api/alembic/` | Migration history — the *real* way the DB schema is created/changed, not `create_all()` |
| `api/app/seed.py` | One-time script to insert the 3 fake tenants |
| `api/tests/conftest.py` | Pytest fixtures: spins up a **separate** `relayops_test` database per test, so tests can never touch dev data |
| `api/tests/test_incidents.py` | Tests for create/list/get + the "bad tenant_id" error case |
| `web/src/lib/api.ts` | Typed API client — fetches incidents and validates the shape with **Zod at runtime** |
| `web/src/app/page.tsx` | Renders the incident queue |
| `docs/adr/0001-deterministic-core.md` | The core design rule: the model may *suggest*, the app code owns state/side-effects |

---

## 3. Concepts worth actually understanding (not memorizing)

- **Monorepo**: one Git repo, multiple independently-runnable projects
  (`api/`, `web/`). They don't share a build step; they just live together.

- **uv**: Python package/dependency manager. `uv init` defaults to a
  *library* layout (`src/api/`); we wanted an *application* layout, so we
  removed `src/` and set `package = false` under `[tool.uv]` in
  `pyproject.toml`.

- **SQLModel**: one class (`Incident`, `Tenant`, etc.) defines both the
  Postgres table *and* the Pydantic validation shape. Less duplication,
  but you have to be careful not to expose DB-only fields to the API by
  accident — that's why `schemas.py` exists as a separate, deliberate layer.

- **Alembic migrations vs. `create_all()`**: `SQLModel.metadata.create_all()`
  is fine for a first prototype, but it can't *change* an existing table
  (add a column, rename something) without you dropping and recreating data.
  Alembic tracks schema changes as versioned, runnable scripts — the
  professional way to evolve a real database over time.

- **Dependency injection in FastAPI** (`Depends(get_session)`): each request
  gets its own DB session, automatically opened and closed. Routes just
  declare "give me a session" and don't worry about lifecycle.

- **Why a separate test database**: `conftest.py` points tests at
  `relayops_test`, not your real `relayops` dev database, and wipes/recreates
  tables around every single test (`autouse=True` fixture). This means
  tests are isolated from each other AND can never corrupt real dev data.

- **Foreign key constraints as a safety net**: Postgres itself refuses to
  insert an `Incident` row pointing at a `tenant_id` that doesn't exist.
  We initially let that raw database error crash out as an unhandled
  exception (visible in tests as a raw traceback, not a clean assertion
  failure) — then fixed it explicitly in the route:

  ```python
  try:
      db.commit()
  except IntegrityError:
      db.rollback()
      raise HTTPException(status_code=400, detail="Invalid tenant_id: tenant does not exist")
  ```

  Lesson: **letting a database error propagate unhandled is not the same
  as good error handling.** The API needs to translate DB-level failures
  into deliberate, documented HTTP responses.

- **Zod validation on the frontend**: TypeScript types vanish at runtime.
  If the backend ever returns a slightly wrong shape (a renamed field, a
  null where a string was expected), TypeScript can't catch that — only a
  runtime check like `Incident.parse(json)` can. `z.infer<typeof Incident>`
  derives the TypeScript type from the same schema, so you're not writing
  the shape twice.

- **React Server Components**: `page.tsx`'s `Home` function is `async` and
  awaits `listIncidents()` directly — no `useEffect`/loading state needed
  for this case, because the fetch happens server-side before any HTML is
  sent.

- **Operational dependency (the "kill the API" test)**: with the API down,
  the frontend didn't degrade gracefully — it threw a hard
  `ECONNREFUSED` error and rendered nothing useful. This is expected and
  intentional to observe at this stage; graceful degradation is a later
  concern, not a Gate 1 requirement.

---

## 4. The gotchas we actually hit (and why)

| Symptom | Root cause | Fix |
|---|---|---|
| `zsh: no matches found: psycopg[binary]` | zsh treats `[binary]` as a glob pattern | Quote it: `"psycopg[binary]"` |
| `role "relayops" does not exist` | A native (Homebrew) Postgres was running on port 5432, stealing the connection from Docker's Postgres | Remapped Docker Postgres to port **5433** in `compose.yaml` + `.env` |
| `ModuleNotFoundError: No module named 'app'` (pytest) | Pytest doesn't add the cwd to `sys.path` by default | Added `pythonpath = ["."]` under `[tool.pytest.ini_options]` in `pyproject.toml` |
| `NameError: name 'sqlmodel' is not defined` in an Alembic migration | Auto-generated migration used `sqlmodel.sql.sqltypes.AutoString()` but forgot to import `sqlmodel` | Added `import sqlmodel` manually to the migration file |
| `ruff` wanted to delete `from app import models` in `alembic/env.py` | Looks "unused" statically, but it's what makes `SQLModel.metadata` aware of your tables | Added `# noqa: F401` — a deliberate, commented exception, not a blind auto-fix |
| Unhandled `IntegrityError` crashing a test instead of failing an assertion | No explicit handling of FK violations in the route | Added `try/except IntegrityError` → `HTTPException(400, ...)` |
| `make web` failed: "Node.js 18.20.8 ... >=20.9.0 required" | `nvm`'s `default` alias still pointed at an old Node 18 install | `nvm alias default 24` (had to re-run per terminal until reopened) |
| `web/.env.local(.example)` literally contained the text `.env.local.example` | Copy-paste mistake during scaffolding | Rewrote both files with the real `NEXT_PUBLIC_API_BASE_URL` value; also had to punch a hole in `web/.gitignore` (`!.env.local.example`) since Next's default `.gitignore` blocks `.env*` entirely |

---

## 5. Runbook — commands you'll actually reuse

```bash
# Start/stop the database (Docker)
make db-up
make db-down

# Run the backend (from repo root)
make api          # -> http://localhost:8000, docs at /docs

# Run the frontend (from repo root)
make web          # -> http://localhost:3000

# Run backend tests + linter
make test
make lint

# Look at a table directly
docker compose exec db psql -U relayops -d relayops -c "SELECT * FROM tenant;"

# Create a new Alembic migration after changing api/app/models.py
cd api && uv run alembic revision --autogenerate -m "describe the change"
uv run alembic upgrade head
```

---

## 6. How we proved Gate 1 actually passed

1. Created an incident through the `/docs` Swagger UI (not just curl —
   proving the real HTTP contract works, including validation).
2. Refreshed `localhost:3000` and saw the new incident render.
3. **Restarted both the API and the frontend** and confirmed the incident
   was still there — the only way that's possible is if it's really in
   Postgres, not sitting in server memory.
4. Killed the API only, refreshed the frontend, and watched it fail
   loudly (`ECONNREFUSED`) — confirming the dependency is real, not
   accidentally mocked or cached away.
5. `uv run pytest -q` → 4 passed. `uv run ruff check .` → clean.
   `pnpm lint` → clean.

---

## 7. Honest self-check

Could you rebuild this from an empty folder with zero references? Probably
not yet, and that's fine — that's not the bar. The real bar: could you,
with this doc, the ADR, and the Makefile as reference, explain *why* each
piece exists and reconstruct it? That's the skill that transfers to every
future project, long after the exact `uv`/`alembic`/`zod` command syntax is
forgotten.
