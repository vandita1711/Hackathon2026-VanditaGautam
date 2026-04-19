# ShopWave Architecture (1-Page)

## System Diagram

```mermaid
flowchart TD
		A[Ticket Input\nUI or CLI] --> B[Orchestrator\nprocess_ticket]
		B --> C{LLM Enabled\nand Provider Ready?}

		C -- Yes --> D[AutoGen Team Loop\nPlanner -> Executor -> Critic]
		C -- No --> H[Deterministic Engine]

		D --> E[Tool Calls via\nToolRegistry]
		E --> F[Tool Results\nOrder, Refund, Policy, Knowledge]
		F --> G[Critic Review\nStatus + Confidence + Message]
		G --> I{Hard Rules\n& Confidence Gate}

		H --> I

		I --> J[Final Resolution\nresolved or escalate]
		J --> K[Audit Logger\nartifacts/audit_log.json]
		J --> L[UI Table + Trace\n/ CLI Output]

		subgraph Memory and State
			M1[Per-ticket Memory\napp/core/memory.py]
			M2[Ticket Context\ncustomer + order + tool outputs]
			M3[Lifecycle Cleanup\nmemory.clear(ticket_id)]
		end

		B --> M1
		M1 --> M2
		J --> M3
```

## Agent Loop

1. Planner interprets the ticket intent and drafts a tool plan.
2. Executor runs approved tools using deterministic implementations.
3. Critic validates policy compliance, confidence, and customer messaging.
4. Orchestrator parses final response and applies safety gates.
5. If any failure occurs, deterministic fallback is executed.

## Tool Design

- Tools are registered centrally in the ToolRegistry.
- Each tool has a narrow, auditable responsibility:
	- Order retrieval/status tools.
	- Refund and eligibility tools.
	- Policy/knowledge lookup tools.
	- Communication response helpers.
- Tool outputs are structured so critic and fallback logic can reason consistently.

## Memory and State Management

- Per-ticket memory is created at orchestration start.
- Working state includes ticket payload, customer profile, tool outputs, and resolution draft.
- AuditLogger captures event timeline for explainability.
- Memory is cleared in a `finally` block to avoid state leakage across tickets.

## Execution Modes

- AutoGen mode: used when LLM settings are available and valid.
- Deterministic mode: used when LLM is disabled or runtime failures occur.
- Batch processing uses async fan-out in the ticket pipeline for concurrent ticket throughput.
