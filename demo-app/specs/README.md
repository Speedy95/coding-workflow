# specs/

SDLC workflow state — one folder per feature (`NNN-kebab-name/` with spec.md,
plan.md, verification.md, status.json) plus `metrics.jsonl`, the append-only
outcome ledger. Managed by the `/sdlc:*` commands; see the sdlc plugin's
`sdlc-state` skill for the schema.
