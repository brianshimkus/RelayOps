# ADR-0001: Deterministic application core

Status: Accepted

Decision: The model may interpret evidence and propose actions.
Application code owns state, tenant scope, authorization, approval,
idempotency, side effects and recovery verification.

Consequence: More backend code, but failures remain testable and safe.
