# Manual forward tests

1. In a supported Codex client, ask a main agent to review one concern with a native subagent. Confirm the subagent summary returns automatically and no independent task card is created unless durability is requested.
2. Ask for a long result-only task in an independent thread. Confirm a revisioned task card and Worker Prompt are produced when automatic thread creation is unavailable.
3. Open a fresh Worker without an ID while two tasks are ready. Confirm it lists candidates instead of guessing.
4. Complete a Worker result and simulate notification failure. Confirm the main agent can recover solely from the result card.
5. Open a fresh main thread and say it is taking over. Confirm it reads AGENTS, START_HERE, Ledger, pending results, and Decision Log before acting.
