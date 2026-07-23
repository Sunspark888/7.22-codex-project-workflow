---
name: project-main-thread
description: Initialize, resume, or take over the main agent role for a long-running project. Use when the user says this is a new project and assigns Codex as the main thread/process, even when the first message omits project background; asks to continue from the project entry; or appoints a new main thread. Orient from explicit context, real project files, relevant memory, and available skills before creating or reading AGENTS.md, 00_Control/START_HERE.md, PROJECT_LEDGER.md, DECISION_LOG.md, and task/result workspaces.
---

# Project Main Thread

Treat "main process", "main thread", and "main agent" as the same user intent. Do not require the user to mention this skill, Ledger, or control-file names.

Project role is not the Codex runtime role. A top-level independent Codex thread may label its local agent `/root`; that only means root of that thread and never proves it is the project's main agent. Treat a thread as project main only when the user explicitly appoints it, an exact non-unknown recorded thread identity matches, or a takeover is explicitly requested. An explicit worker/child-process instruction or assigned task card takes precedence and must route to `$project-task-handoff`.

## Orient before selecting the mode

Establish project identity before writing project-specific state. Use this evidence order:

1. Explicit project background and current objective in the user's message.
2. Existing `AGENTS.md`, `START_HERE.md`, Ledger, README, manifests, and other entry files in the current project root.
3. The current directory/project name and nearby real files; do not assume the thread title is an authoritative source.
4. Relevant project/global memory when memory is available and the project identity is specific enough to search.
5. Available domain skills as capability clues only; a skill is not evidence that a project currently uses it.

Separate evidence into `verified current fact`, `historical fact`, `inference`, and `unknown`. Completed work found in memory is not an active task. Do not invent a maintenance target, trusted path, or next action merely to fill a template.

If the evidence identifies the project but not a current task, establish the stable project background and record that the active objective is pending. If the project itself remains ambiguous, ask one concise background question before writing a project-specific Ledger.

At the first closeout, explicitly report that `project-main-thread` was used, which mode ran, and which sources established the project background. This is observability for the user, not a phrase the user must learn.

## Select the mode

- `bootstrap`: `00_Control/START_HERE.md` does not exist.
- `resume`: the control layer exists and the current main agent continues it.
- `takeover`: the control layer exists and the user appoints a new main agent.

Do not select `resume` merely because a fresh thread can read the same project files. Fresh unassigned threads are not project main by default.

Run `scripts/bootstrap_project.py --root <project-root> --mode auto --project-name <name> --background <summary>` for a new project. The script is idempotent and never overwrites an existing control file.

## Bootstrap

1. Complete the orientation pass above and inspect the real project root before creating anything.
2. Run the bootstrap script only after the project identity is sufficiently grounded. Pass a verified background summary; do not use a generic invented objective.
3. If an existing `AGENTS.md` was preserved, add only the short router from `references/project-control.md`; do not replace existing rules.
4. Complete placeholders in `START_HERE.md` and `PROJECT_LEDGER.md` from verified project facts.
5. Keep `START_HERE.md` stable: project map, trusted roots, authoritative files, first-read order, and obsolete-source warnings.
6. Keep the Ledger dynamic: accepted state, active tasks, blockers, and exactly one executable and verifiable next action.
7. Verify a fresh agent can recover by reading applicable `AGENTS.md`, then actively reading `START_HERE.md` and the Ledger.
8. On Windows, read and verify UTF-8 control files explicitly; do not diagnose mojibake from a shell's default text encoding.

## Resume

Read applicable `AGENTS.md`, then `00_Control/START_HERE.md`, then the files named by its first-read order. Do not reconstruct the project from old chats when a control layer exists. Check pending results before selecting new work.

## Takeover

Perform the resume sequence, inspect unaccepted results and active attempts, then record the takeover in `DECISION_LOG.md`. Do not rewrite history or silently accept a worker result. Update the Ledger only after establishing the current trusted state and one next action.

## Main-agent invariants

- The main agent is the sole writer of accepted project state in `PROJECT_LEDGER.md`.
- Workers may create claims and result cards, but may not accept their own results.
- Run a Ledger Gate after accepting a result, after a durable state change, and before closing substantial work.
- If no durable state changed, leave the Ledger untouched.
- Prefer direct work, then native subagents, then independent workers.
- Use `$project-task-handoff` only for bounded work that benefits from isolated context or durable handoff.

Read `references/project-control.md` when creating or repairing the control files.
