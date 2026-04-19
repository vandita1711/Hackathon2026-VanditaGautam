## Upgraded Architecture (v2.0)

### 1. Multi-Agent Conversation (AutoGen)
The system now uses **AutoGen** to manage agent interactions:
- **Planner (AssistantAgent)**: Formulates the strategy and suggests tool calls.
- **Executor (UserProxyAgent)**: Acts as the "system" layer, executing Python tools registered in the `ToolRegistry`.
- **Critic (AssistantAgent)**: Reviews the execution results and final resolution against policies.
- **GroupChat Manager**: Orchestrates the speaker order and manages the conversation history.

### 2. LLM Backend (Groq or fallback)
The system prefers **Groq's Llama-3-70b** model when `GROQ_API_KEY` is configured. `config/autogen_config.py` manages whether the app uses Groq or falls back to OpenAI/NextToken.
- If `ENABLE_LLM=false`, the system skips LLM review and uses deterministic policy execution.
- If a configured Groq key is invalid, the orchestrator falls back to deterministic execution automatically.

### 3. Gradio Interface
The `ui_app.py` provides a batch analysis dashboard where users can:
- Batch-process uploaded JSON datasets.
- Inspect the raw JSON audit trace from the ticket run.
- View summary metrics on resolution vs escalation.

### 2. Orchestration & Concurrency
- **The Orchestrator**: Wraps the Agent Trio in a managed lifecycle. It handles per-ticket `Memory` and logs to the `AuditLogger`.
- **Async Pipeline**: The `process_tickets` pipeline uses `asyncio.gather` to execute multiple Orchestrator instances in parallel, maximizing throughput without sacrificing reasoning depth per ticket.

### 3. Knowledge Base Integration
- **Deterministic Policy Retrieval**: Instead of relying on LLM internal knowledge, the `knowledge_tools` fetch ground-truth text from `policies.txt` based on ticket keywords.

### 4. Safety Logic & Confidence
- **Confidence Service**: If the Critic returns a score < 0.6, the system automatically switches the status to `escalate`, regardless of the proposed resolution.
- **Hard Constraints**: Logic in `refund_tools.py` prevents auto-approval of refunds > $200, overriding the LLM's autonomy for high-risk actions.

### 5. Audit Logging
- **Explainability**: Every state change (Planned -> Executed -> Criticized) is saved with timestamps and full raw data in `artifacts/audit_log.json`.
