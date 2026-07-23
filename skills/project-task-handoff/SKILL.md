---
name: project-task-handoff
description: Delegate, execute, converse within, deliver, or accept a bounded task using revisioned task cards, attempt claims, and result cards. Use when the user asks for a child process/thread (子进程/子线程), independent Worker, isolated long or result-only task, a separate worker for direct multi-turn conversation, to return to the main thread, or when a main agent receives a worker result. Prefer native Codex subagents for automatic background return; use file-based handoff for independent user-facing threads without assuming a parent-child relationship.
---

# Project Task Handoff

Hide protocol details from the user. Interpret natural requests such as "give this work to a child thread", "you are the worker", and "finish and return to the main thread".

## Resolve project role first

- An explicit worker/child-process instruction or exact assigned task path establishes the thread as an independent Worker for that task.
- Codex runtime labels such as `/root` describe the local agent tree inside the current thread; they do not make this thread the project's main agent.
- A readable project Ledger or `project-state.json` does not grant main-agent authority. `main_thread_id: unknown` grants no identity at all.
- Worker intent takes precedence over generic project-resume behavior. Do not invoke `$project-main-thread` in a thread explicitly launched as a Worker.
- If role remains ambiguous and no task is assigned, stop and ask one concise role/assignment question. Never self-promote to project main.

## Choose the execution type

Use this order:

1. Main agent directly performs short or tightly coupled work.
2. Native subagent performs independent parallel review, testing, search, or disjoint implementation and returns automatically.
3. Independent worker uses task/result files when work is long, result-oriented, recoverable, or should have isolated context.

When the user wants to talk directly with the delegated agent over multiple turns, choose an independent Worker thread. A native subagent is for background execution and automatic return, not a substitute for a user-facing conversation thread.

Do not describe an independent Codex thread as a native subagent. Do not assume a parent-child API exists.

## Dispatch mode

1. Read `START_HERE.md` and the Ledger.
2. Confirm that the work is bounded, mostly result-returning, and safe to isolate.
3. Run `scripts/taskctl.py new` to generate the task ID and revisioned contract.
4. Fill the generated task contract with necessary facts, allowed reads/writes, forbidden actions, acceptance criteria, and result expectations.
5. As the main agent, add the task ID, revision, and current status to the Ledger's active-task index.
6. Prefer a native subagent when durable independent-thread recovery is unnecessary.
7. If the user explicitly requested a separate thread and the client exposes a thread-creation tool, create it and pass the exact task path in its initial prompt. Record the returned thread identifier when available.
8. Say "thread created" only after the creation tool returns success and an identifier/reference. Creating a task card or printing a Worker greeting is not thread creation.
9. If no creation tool is available, say "task card created; worker thread not yet created" and give the user one copyable Worker Prompt from `references/worker-prompt.md`.
10. Never impersonate the Worker by continuing its dialogue inside the main thread.

## Worker mode

1. Read applicable `AGENTS.md`, then `START_HERE.md`.
2. Claim the explicit task with `taskctl.py claim --task-id <id>`. If no ID was provided, auto-claim only when exactly one ready task exists; list candidates and stop when there are several.
3. Read only the assigned task contract and its allowed project sources. Do not read the main thread history.
4. Do not modify the Ledger, Decision Log, or task contract.
5. Create a result template with `taskctl.py result`, complete it, run the required verification, then mark it delivered with `taskctl.py deliver`.
6. Treat cross-thread notification as optional. The result card is the reliable handoff.
7. When the user says "finish and return to the main thread", stop expanding scope and deliver. When they say "pause and return", record a blocked or partial result.
8. On Windows, read UTF-8 Markdown explicitly; do not infer file corruption from the shell's default encoding.
9. For a conversational assignment, stay in Worker role across turns and ask only questions allowed by the task contract. Do not deliver until the user ends the dialogue, the acceptance condition is met, or a blocker requires return.

## Accept mode

1. Verify task ID, revision, attempt ID, artifacts, and evidence.
2. Reject automatic acceptance when the result targets an old revision.
3. Run `taskctl.py decide --decision accepted|rework|canceled` only after main-agent review.
4. Update or remove the task in the Ledger's active-task index after the decision.
5. Update other Ledger sections only if accepted project state, blockers, or the unique next action changed.
6. Record material reasoning in `DECISION_LOG.md`.

## Invariants

- Task identity survives retries; attempt identity does not.
- Task contracts are revisioned and never overwritten.
- One result card belongs to one attempt and is never overwritten.
- Worker `delivered` does not mean main-agent `accepted`.
- Notification failure never invalidates a valid result card.
- A task card without a successful thread-creation result is `ready`, not evidence of a running Worker.
- Never represent text generated in the main thread as a message from a newly created Worker.
- Do not introduce a database, queue service, lock server, or persistent coordinator for this local workflow.

Run `scripts/taskctl.py validate --root <project-root>` after protocol changes or before declaring the handoff complete.
