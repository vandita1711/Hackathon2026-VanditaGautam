# ShopWave Failure Modes & Resilience

| Failure Scenario | System Handling | Mitigation Component |
|------------------|-----------------|----------------------|
| **LLM Hallucination** | Planner suggests a tool that doesn't exist. | `ToolRegistry` catches the KeyError; `Executor` logs the error; `Critic` sees the failed execution and escalates. |
| **API Timeout** | A tool call (simulated) hangs for 5+ seconds. | `RetryHandler` attempts exponential backoff (3 retries). If it still fails, the `Executor` reports a timeout result. |
| **Policy Boundary** | Agent tries to refund $250 for a VIP customer. | `execute_refund` tool has a hard-coded check against `MAX_REFUND_AUTO_APPROVE`. It forces an 'Escalation Required' result. |
| **Conflicting Data** | Order says 'Shipped' but customer claims 'Not received'. | `Critic` identifies the risk in the `execution_results` and triggers an escalation due to 'Conflicting Records' policy. |
| **Malformed Response** | LLM returns non-JSON text in a JSON-mode request. | `Planner`/`Critic` catch blocks with `try-except` on `json.loads`. Default action is to `escalate` for safety. |
| **Invalid LLM Key** | `GROQ_API_KEY` is missing or invalid, or the external LLM call fails. | `Orchestrator` logs the failure and falls back to deterministic execution, preserving customer support continuity. |
| **Out-of-Window** | Customer asks for refund after 45 days. | `check_refund_eligibility` performs deterministic date math. It returns 'Ineligible', preventing the `Executor` from even trying to refund. |
