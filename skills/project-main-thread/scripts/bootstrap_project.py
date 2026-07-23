#!/usr/bin/env python3
"""Create an idempotent Markdown control layer for a long-running project."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path


def slugify(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return value or "project"


def write_new(path: Path, content: str, created: list[str], preserved: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        created.append(str(path))
    except FileExistsError:
        preserved.append(str(path))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--mode", choices=("auto", "bootstrap", "resume", "takeover"), default="auto")
    parser.add_argument("--project-name", default="Long-running project")
    parser.add_argument("--background", default="To be completed from verified project facts.")
    parser.add_argument("--main-thread-id", default="unknown")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    control = root / "00_Control"
    start = control / "START_HERE.md"
    mode = ("resume" if start.exists() else "bootstrap") if args.mode == "auto" else args.mode
    if mode in {"resume", "takeover"} and not start.exists():
        raise SystemExit("Control layer is missing; use bootstrap mode first.")

    if mode != "bootstrap":
        print(json.dumps({"mode": mode, "root": str(root), "start_here": str(start)}, ensure_ascii=False))
        return 0

    created: list[str] = []
    preserved: list[str] = []
    now = datetime.now(timezone.utc).isoformat()
    project_id = f"P-{datetime.now().strftime('%Y%m%d')}-{slugify(args.project_name)}"
    (control / "tasks").mkdir(parents=True, exist_ok=True)
    (control / "results").mkdir(parents=True, exist_ok=True)

    write_new(root / "AGENTS.md", """# Project agent rules

## Long-running project entry

- Before project work, actively read `00_Control/START_HERE.md`, then follow its first-read order.
- The main agent is the only writer of accepted state in `00_Control/PROJECT_LEDGER.md`.
- Independent workers read an assigned task card and write claims/results only; they do not accept results or edit the Ledger.
- Project role comes from explicit appointment or assignment, not the Codex runtime `/root` label. An explicit Worker task overrides generic resume behavior.
- Durable decisions go to `00_Control/DECISION_LOG.md`.
""", created, preserved)
    write_new(start, f"""# START HERE

## Project

- Name: {args.project_name}
- Project ID: `{project_id}`
- Background: {args.background}
- Trusted root: `{root}`

## First-read order

1. Applicable `AGENTS.md`
2. This file
3. `PROJECT_LEDGER.md`
4. Files explicitly listed under Authoritative sources

## Authoritative sources

- Add verified project documents and code roots here.

## Control files

- Accepted state: `PROJECT_LEDGER.md`
- Decision reasons: `DECISION_LOG.md`
- Task protocol: `TASK_PROTOCOL.md`
- Task contracts: `tasks/`
- Attempt results: `results/`

## Obsolete or unsafe sources

- Add superseded entry files, stale paths, and prohibited recovery sources here.
""", created, preserved)
    write_new(control / "PROJECT_LEDGER.md", """# Project Ledger

## Current goal

Confirm the project facts and establish the first executable work item.

## Accepted state

- The control layer has been initialized; project-specific facts still require verification.

## Active tasks

- None.

## Blockers and risks

- Authoritative project sources have not yet been recorded.

## Current unique next step

Read the existing project files and record the authoritative sources in `START_HERE.md`.
""", created, preserved)
    write_new(control / "DECISION_LOG.md", f"""# Decision Log

## {datetime.now().date().isoformat()} - Initialize project control layer

- Decision: Use a stable project map, an accepted-state Ledger, and file-based worker handoffs.
- Reason: Preserve recoverability without copying full thread history.
- Recorded at: {now}
""", created, preserved)
    write_new(control / "TASK_PROTOCOL.md", """# Task Protocol

## Task states

`draft -> ready -> accepted | rework | canceled`

## Attempt states

`claimed -> delivered | blocked | failed`

The main agent accepts tasks. A worker only claims an attempt and delivers evidence. A changed contract creates a new revision; old results never auto-apply to a newer revision.

Creating a task card does not prove that a Worker thread exists. Report a thread as created only after a client thread-creation tool succeeds. The runtime `/root` label is local to each Codex thread and is not a project role.
""", created, preserved)
    write_new(control / "project-state.json", json.dumps({
        "schema_version": 1,
        "project_id": project_id,
        "project_name": args.project_name,
        "main_thread_id": args.main_thread_id,
        "initialized_at": now,
    }, ensure_ascii=False, indent=2) + "\n", created, preserved)

    print(json.dumps({
        "mode": "bootstrap",
        "root": str(root),
        "created": created,
        "preserved": preserved,
        "needs_agents_merge": str(root / "AGENTS.md") in preserved,
        "start_here": str(start),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
