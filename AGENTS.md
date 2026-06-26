# VoiceOps

FastAPI service with JWT auth (`/auth`) and a deterministic VoiceOps RCA agent
pipeline (`/agents`) that classifies failure logs into root-cause reports.
Persistence is async SQLAlchemy on PostgreSQL; the RCA pipeline is wrapped with
LangGraph. There is no frontend — the GUI is FastAPI's auto-generated Swagger UI
at `/docs`.

## Cursor Cloud specific instructions

The startup update script creates `./venv` and installs Python deps (plus
`pyright` for linting). The following services are NOT started by the update
script and must be started manually each session:

- **PostgreSQL** runs via the committed `docker-compose.yaml` (image
  `postgres:16-alpine`, creds/db `voiceops`, port 5432; matches `.env`).
  Docker is pre-installed in the snapshot but the daemon does not auto-start.
  Start it then bring up Postgres:
  - `sudo dockerd` (run in the background, e.g. a tmux session)
  - `sudo docker compose up -d`
  - Gotcha: Docker is configured with the `fuse-overlayfs` storage driver and
    `containerd-snapshotter` disabled (`/etc/docker/daemon.json`) — required for
    Docker to work in this VM. Don't switch to overlay2.

- **Database schema** is NOT auto-migrated (no Alembic). After the first
  `docker compose up` on a fresh `postgres_data` volume, apply the schema once:
  `cat schema/basic.sql | sudo docker exec -i voiceops_postgres psql -U voiceops -d voiceops`
  The named volume persists across container restarts, so re-applying is only
  needed if the volume is recreated.

- **API dev server** (needs Postgres up first):
  `./venv/bin/uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000`
  Open Swagger UI at `http://localhost:8000/docs`.

### Lint / test

- Lint: `./venv/bin/pyright` (config in `pyrightconfig.json`).
- Tests: `./venv/bin/python -m unittest discover -s tests` (uses `unittest`,
  not pytest; the RCA tests are pure-Python and need no database).

### Notes

- `app.api.db.session` raises at import if `DATABASE_URL` is unset; `.env` is
  committed and loaded via `python-dotenv`, so run from the repo root.
- Agent runs execute in a FastAPI `BackgroundTask`; `POST /agents/run` returns
  immediately with `status: pending` — poll `GET /agents/run/{run_id}` for the
  completed RCA `result`.
