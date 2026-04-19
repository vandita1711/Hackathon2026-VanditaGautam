# ShopWave Failure Mode Analysis

This document covers concrete failure scenarios and how the system responds safely.

## Scenario 1: LLM Provider Failure (429/401/timeout)

- Trigger:
	- Rate limit reached, invalid API key, or request timeout from provider.
- Detection:
	- Exception raised in AutoGen run path.
- System response:
	- Orchestrator logs `autogen_failed` and immediately executes deterministic fallback.
	- Ticket still receives a final resolution payload (status, confidence, message).
- User impact:
	- No hard outage for ticket processing; only reduced LLM quality.

## Scenario 2: Malformed LLM Output (invalid JSON)

- Trigger:
	- Agent returns non-JSON or mixed content when JSON output is expected.
- Detection:
	- Parse failure in orchestration parser.
- System response:
	- Parser attempts safe extraction of JSON object.
	- If parsing still fails, orchestration moves to deterministic fallback.
	- Failure details are logged in audit trace for debugging.
- User impact:
	- Resolution still produced; problematic LLM output does not break run.

## Scenario 3: Policy Boundary Violation (high-value refund)

- Trigger:
	- Refund request exceeds `MAX_REFUND_AUTO_APPROVE` threshold.
- Detection:
	- Hard-rule check in deterministic policy path.
- System response:
	- Auto-approval is blocked.
	- Case is forced to `escalate` with supervisor team routing.
- User impact:
	- Safe policy-compliant handling for financial risk cases.

## Scenario 4: Missing or Inconsistent Ticket Inputs

- Trigger:
	- Ticket missing order ID, unknown customer identity, or inconsistent records.
- Detection:
	- Planner/executor checks and policy checks fail to verify key entities.
- System response:
	- System requests clarification when safe to continue.
	- Escalates when identity or fraud risk is present.
- User impact:
	- No silent failure; customer gets actionable next step.

## Scenario 5: Data File Parsing Errors (upload path)

- Trigger:
	- Uploaded JSON includes UTF-8 BOM, malformed JSON, or wrong payload shape.
- Detection:
	- Data loader validates file format and raises explicit errors.
- System response:
	- UI shows clear error status instead of silently loading empty data.
	- Processing is blocked until data is valid.
- User impact:
	- Faster debugging and reduced risk of hidden empty-dataset runs.

## Summary

The system prioritizes continuity (fallback), safety (hard policy gates), and observability (audit logging) across operational, model, and data failures.
