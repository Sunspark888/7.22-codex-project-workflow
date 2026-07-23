# Project control contract

## Project-level AGENTS.md router

Add this block without replacing existing project rules:

```markdown
## Long-running project entry

- Before project work, actively read `00_Control/START_HERE.md`, then follow its first-read order.
- The main agent is the only writer of accepted state in `00_Control/PROJECT_LEDGER.md`.
- Independent workers read an assigned task card and write claims/results only; they do not accept results or edit the Ledger.
- Project role comes from explicit appointment or assignment, not the Codex runtime `/root` label. An explicit Worker task overrides generic resume behavior.
- Durable decisions go to `00_Control/DECISION_LOG.md`.
```

## File responsibilities

- `AGENTS.md`: behavior and boundaries.
- `START_HERE.md`: stable project map and reading order.
- `PROJECT_LEDGER.md`: dynamic accepted state and one next action.
- `DECISION_LOG.md`: material decisions and reasons.
- `TASK_PROTOCOL.md`: task/attempt state meanings.
- `tasks/`: immutable revisioned task contracts and claim records.
- `results/`: one result card per attempt.

Never duplicate dynamic accepted state in `START_HERE.md`. Link to the Ledger instead.
