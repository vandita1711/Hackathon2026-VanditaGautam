# ShopWave: Autonomous Support Resolution Agent

Production-minded support agent for customer ticket resolution using planner/executor/critic orchestration with deterministic policy guardrails.

## 1. Working Agent (Runnable)

### Clear entry points
- Main CLI entry point: `main.py`
- Demo runner: `run_demo.py`
- UI entry point: `ui_app.py`
- Windows launcher: `start_ui.ps1`

### Environment setup
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

### Run from CLI (single clear entry path)
```bash
python main.py --demo
```

### Run with UI
```bash
python ui_app.py
```

On Windows PowerShell (recommended):
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\start_ui.ps1
```

UI URL: `http://127.0.0.1:7860`

## 2. Project Deliverables Mapping

- Architecture diagram document: `docs/architecture.md`
- Failure mode analysis: `docs/failure_modes.md`

## 3. Runtime Behavior

- AutoGen path is attempted first when LLM is enabled and credentials are valid.
- If LLM fails (invalid key, timeout, rate-limit), the system falls back to deterministic logic.
- Every ticket run is audited in `artifacts/audit_log.json`.

## 4. LLM Setup

- Add `GROQ_API_KEY=...` in `.env` for Groq-backed agent reasoning.
- Optional fallback provider:
	- `OPENAI_API_KEY=...`
	- `OPENAI_BASE_URL=https://api.openai.com/v1`
- Deterministic-only mode:
	- `ENABLE_LLM=false`

## 5. Core Structure

- `app/agents/`: planner, executor, critic, AutoGen wiring.
- `app/core/`: orchestrator, memory, logger.
- `app/services/`: data loading, deterministic engine, LLM engine, audit.
- `app/tools/`: policy, order, refund, communication tool layer.
- `config/`: prompts, settings, provider config.
- `docs/`: architecture and failure-mode documentation.

## 6. Deploy To GitHub

1. Initialize git at repository root (folder that contains `render.yaml`).
2. Commit project files.
3. Push to GitHub.

Repository layout options supported:
- If your GitHub repo root is this folder (`shopwave_autonomous_agent/`), use the local `render.yaml` in this folder.
- If your GitHub repo root is the parent folder, use the parent-level `render.yaml` (with `rootDir: shopwave_autonomous_agent`).

## 7. Deploy To Render

This project is configured with `render.yaml` for one-click infrastructure config.

1. In Render, create a new Web Service from your GitHub repo.
2. Ensure Render detects and uses `render.yaml`.
3. Confirm service settings:
	- Environment: Python
	- Root Directory:
	  - Leave empty when repo root is this folder.
	  - Set to `shopwave_autonomous_agent` when repo root is the parent folder.
	- Build Command: `pip install -r requirements.txt`
	- Start Command: `python ui_app.py`
4. Deploy.

Notes:
- The app now auto-binds to Render's `PORT` and `0.0.0.0`.
- Local fallback still uses `127.0.0.1` and ports `7860-7864`.
- LLM is disabled by default in `render.yaml` for stable demo behavior; deterministic fallback remains active.

## 8. Avoid Manifest/Assets 404 In Render

If you previously saw errors like missing `/manifest.json` or `/assets/*.js`:

1. Redeploy after latest commit.
2. Open the app URL in an incognito window (or hard refresh with cache clear).
3. Confirm only one active Render deployment is serving traffic.

Why this is fixed now:
- Startup uses Render-compatible host/port.
- Dependency versions are pinned for deterministic frontend asset builds.
- Repo-local `.local` package shadowing is disabled by default to prevent stale Gradio asset sets from being imported.

