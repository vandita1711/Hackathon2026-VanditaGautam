# ShopWave: Autonomous Support Resolution Agent

A production-minded, modular support agent built for the 2026 Hackathon. It uses a planner/executor/critic style workflow to resolve customer tickets while enforcing strict business policies.

## Launching the System

### Option A: Command Line Demo
```bash
cp .env.example .env
# add GROQ_API_KEY to .env when you want live Groq-backed review
export PYTHONPATH=$PYTHONPATH:.
python3 run_demo.py
```

### Option B: Interactive Dashboard (Gradio)
```bash
python3 ui_app.py
```

Access the UI at `http://localhost:7860`. Upload your JSON data files in the first tab, then run the agent analysis.

On Windows, prefer:
```powershell
.\start_ui.ps1
```

That launcher stops any stale process already using port `7860` and starts the UI from the project `venv`, which avoids old-code / wrong-interpreter issues.

## Architecture
- Deterministic tool execution for policy-safe support actions.
- Optional Groq-backed LLM review layer for richer reasoning and customer messaging.
- Audit logging for every planning, tool, and resolution step.
- Concurrent ticket processing for demo batches.

## Project Structure
- `app/agents/`: agent and execution helpers.
- `app/tools/`: order, refund, policy, and communication tools.
- `app/core/`: orchestration and memory.
- `app/services/`: audit logging, confidence scoring, data loading, deterministic and LLM engines.
- `config/`: prompts and business rules.
- `artifacts/`: audit logs and debug output.

## LLM Setup
- Copy `.env.example` to `.env`.
- Add `GROQ_API_KEY=...` to enable Groq-backed review and response enhancement.
- If you want a secondary fallback provider, add `OPENAI_API_KEY=...` and `OPENAI_BASE_URL=https://api.openai.com/v1`.
- Remove any leading spaces in `.env` values so the keys are parsed correctly.
- Set `ENABLE_LLM=false` in `.env` if you want deterministic mode only.
- If `GROQ_API_KEY` is missing or invalid, the app will fall back to OpenAI (if configured) or deterministic policy logic automatically.
