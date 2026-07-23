#!/usr/bin/env python3
"""Small, dependency-free task-card generator and validator."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

TASK_HEADINGS = ("## Objective", "## Necessary facts", "## Allowed reads", "## Allowed writes", "## Forbidden actions", "## Acceptance criteria", "## Return requirements")
RESULT_HEADINGS = ("## Outcome", "## Core conclusions", "## Artifacts", "## Verification", "## Remaining risks", "## Recommended next step")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def slugify(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return value or "task"


def control(root: str) -> Path:
    path = Path(root).expanduser().resolve() / "00_Control"
    if not (path / "START_HERE.md").exists():
        raise SystemExit(f"Missing project entry: {path / 'START_HERE.md'}")
    return path


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def replace_json(path: Path, data: dict) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def require_headings(path: Path, headings: tuple[str, ...]) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return [heading for heading in headings if heading not in text]


def state_paths(ctrl: Path) -> list[Path]:
    return sorted((ctrl / "tasks").glob("T-*/state.json"))


def select_ready(ctrl: Path, task_id: str | None) -> tuple[Path, dict]:
    def available(state: dict) -> bool:
        statuses = {
            item["status"]
            for item in state.get("attempts", {}).values()
            if item.get("revision") == state["current_revision"]
        }
        return state["task_status"] == "ready" and not statuses.intersection({"claimed", "delivered"})

    if task_id:
        path = ctrl / "tasks" / task_id / "state.json"
        if not path.exists():
            raise SystemExit(f"Unknown task: {task_id}")
        state = read_json(path)
        if not available(state):
            raise SystemExit(f"Task is not available: {state['task_status']}")
        return path, state
    candidates = [(path, read_json(path)) for path in state_paths(ctrl)]
    candidates = [(path, state) for path, state in candidates if available(state)]
    if len(candidates) != 1:
        ids = [state["task_id"] for _, state in candidates]
        raise SystemExit(f"Expected exactly one ready task; found {len(ids)}: {', '.join(ids) or 'none'}")
    return candidates[0]


def cmd_new(args: argparse.Namespace) -> None:
    ctrl = control(args.root)
    date = datetime.now().strftime("%Y%m%d")
    existing = [int(match.group(1)) for path in (ctrl / "tasks").glob(f"T-{date}-*-*") if (match := re.match(rf"T-{date}-(\d{{3}})-", path.name))]
    task_id = f"T-{date}-{max(existing, default=0) + 1:03d}-{slugify(args.slug)}"
    task_dir = ctrl / "tasks" / task_id
    task_dir.mkdir(parents=True, exist_ok=False)
    (task_dir / "claims").mkdir()
    (ctrl / "results" / task_id).mkdir(parents=True, exist_ok=False)
    revision = 1
    contract = task_dir / f"task-r{revision:03d}.md"
    contract.write_text(f"""# Task {task_id} r{revision:03d}

## Objective

{args.objective}

## Necessary facts

- Add no more than five execution-critical facts.

## Allowed reads

- Add exact paths.

## Allowed writes

- None unless explicitly listed.

## Forbidden actions

- Do not read the main thread history or edit `PROJECT_LEDGER.md`.

## Acceptance criteria

- Add observable and verifiable completion criteria.

## Return requirements

- Complete one result card for the claimed attempt, including evidence and risks.
""", encoding="utf-8", newline="\n")
    state = {"schema_version": 1, "task_id": task_id, "task_status": "ready", "current_revision": revision, "created_at": now(), "attempts": {}}
    (task_dir / "state.json").write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"task_id": task_id, "revision": revision, "contract": str(contract)}, ensure_ascii=False))


def cmd_claim(args: argparse.Namespace) -> None:
    ctrl = control(args.root)
    state_path, state = select_ready(ctrl, args.task_id)
    task_dir = state_path.parent
    used = [int(p.stem[1:]) for p in (task_dir / "claims").glob("A[0-9][0-9].json")]
    attempt_id = f"A{max(used, default=0) + 1:02d}"
    claim = {"task_id": state["task_id"], "revision": state["current_revision"], "attempt_id": attempt_id, "attempt_status": "claimed", "thread_id": args.thread_id, "claimed_at": now()}
    claim_path = task_dir / "claims" / f"{attempt_id}.json"
    with claim_path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(claim, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    state["attempts"][attempt_id] = {"status": "claimed", "revision": state["current_revision"]}
    replace_json(state_path, state)
    contract = task_dir / f"task-r{state['current_revision']:03d}.md"
    print(json.dumps({"task_id": state["task_id"], "revision": state["current_revision"], "attempt_id": attempt_id, "contract": str(contract)}, ensure_ascii=False))


def cmd_result(args: argparse.Namespace) -> None:
    ctrl = control(args.root)
    state_path = ctrl / "tasks" / args.task_id / "state.json"
    state = read_json(state_path)
    claim_path = state_path.parent / "claims" / f"{args.attempt_id}.json"
    if not claim_path.exists():
        raise SystemExit("Attempt has not been claimed.")
    result = ctrl / "results" / args.task_id / f"{args.attempt_id}.md"
    content = f"""# Result {args.task_id} {args.attempt_id}

- Task revision: {state['current_revision']}
- Attempt status: claimed

## Outcome

success | partial | blocked | failed

## Core conclusions

- Add up to five conclusions.

## Artifacts

- Add exact paths or `None`.

## Verification

- Add commands/checks and observed results.

## Remaining risks

- Add risks or `None`.

## Recommended next step

Add one recommendation for the main agent.
"""
    with result.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(content)
    print(json.dumps({"result": str(result)}, ensure_ascii=False))


def cmd_deliver(args: argparse.Namespace) -> None:
    ctrl = control(args.root)
    state_path = ctrl / "tasks" / args.task_id / "state.json"
    state = read_json(state_path)
    result = ctrl / "results" / args.task_id / f"{args.attempt_id}.md"
    if not result.exists():
        raise SystemExit("Result card is missing.")
    missing = require_headings(result, RESULT_HEADINGS)
    if missing:
        raise SystemExit(f"Result card missing headings: {', '.join(missing)}")
    claim_path = state_path.parent / "claims" / f"{args.attempt_id}.json"
    claim = read_json(claim_path)
    claim["attempt_status"] = args.status
    claim["outcome"] = args.outcome
    claim["delivered_at"] = now()
    replace_json(claim_path, claim)
    state["attempts"][args.attempt_id] = {"status": args.status, "outcome": args.outcome, "revision": claim["revision"]}
    replace_json(state_path, state)
    print(json.dumps({"task_id": args.task_id, "attempt_id": args.attempt_id, "status": args.status, "outcome": args.outcome, "result": str(result)}, ensure_ascii=False))


def cmd_decide(args: argparse.Namespace) -> None:
    ctrl = control(args.root)
    state_path = ctrl / "tasks" / args.task_id / "state.json"
    state = read_json(state_path)
    delivered_current = any(
        item.get("status") == "delivered" and item.get("revision") == state["current_revision"]
        for item in state.get("attempts", {}).values()
    )
    if not delivered_current and args.decision == "accepted":
        raise SystemExit("Only a delivered attempt for the current revision can be accepted.")
    state["task_status"] = args.decision
    state["decided_at"] = now()
    replace_json(state_path, state)
    print(json.dumps({"task_id": args.task_id, "decision": args.decision}, ensure_ascii=False))


def cmd_revise(args: argparse.Namespace) -> None:
    ctrl = control(args.root)
    state_path = ctrl / "tasks" / args.task_id / "state.json"
    state = read_json(state_path)
    revision = state["current_revision"] + 1
    contract = state_path.parent / f"task-r{revision:03d}.md"
    with contract.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(f"# Task {args.task_id} r{revision:03d}\n\n" + "\n\n".join(f"{h}\n\nTo be completed for revision {revision}." for h in TASK_HEADINGS) + "\n")
    state["current_revision"] = revision
    state["task_status"] = "ready"
    state["revised_at"] = now()
    replace_json(state_path, state)
    print(json.dumps({"task_id": args.task_id, "revision": revision, "contract": str(contract)}, ensure_ascii=False))


def cmd_validate(args: argparse.Namespace) -> None:
    ctrl = control(args.root)
    errors: list[str] = []
    for state_path in state_paths(ctrl):
        try:
            state = read_json(state_path)
            contract = state_path.parent / f"task-r{state['current_revision']:03d}.md"
            if not contract.exists():
                errors.append(f"Missing contract: {contract}")
            else:
                missing = require_headings(contract, TASK_HEADINGS)
                if missing:
                    errors.append(f"{contract}: missing {missing}")
            for attempt, attempt_state in state.get("attempts", {}).items():
                claim = state_path.parent / "claims" / f"{attempt}.json"
                if not claim.exists():
                    errors.append(f"Missing claim: {claim}")
                if attempt_state.get("status") in {"delivered", "blocked", "failed"}:
                    result = ctrl / "results" / state["task_id"] / f"{attempt}.md"
                    if not result.exists():
                        errors.append(f"Missing result: {result}")
        except (KeyError, json.JSONDecodeError) as exc:
            errors.append(f"Invalid state {state_path}: {exc}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        raise SystemExit(1)
    print(json.dumps({"valid": True, "tasks": len(state_paths(ctrl))}))


def parser() -> argparse.ArgumentParser:
    top = argparse.ArgumentParser()
    sub = top.add_subparsers(dest="command", required=True)
    new = sub.add_parser("new"); new.add_argument("--root", required=True); new.add_argument("--slug", required=True); new.add_argument("--objective", required=True); new.set_defaults(func=cmd_new)
    claim = sub.add_parser("claim"); claim.add_argument("--root", required=True); claim.add_argument("--task-id"); claim.add_argument("--thread-id", default="unknown"); claim.set_defaults(func=cmd_claim)
    result = sub.add_parser("result"); result.add_argument("--root", required=True); result.add_argument("--task-id", required=True); result.add_argument("--attempt-id", required=True); result.set_defaults(func=cmd_result)
    deliver = sub.add_parser("deliver"); deliver.add_argument("--root", required=True); deliver.add_argument("--task-id", required=True); deliver.add_argument("--attempt-id", required=True); deliver.add_argument("--status", choices=("delivered", "blocked", "failed"), default="delivered"); deliver.add_argument("--outcome", choices=("success", "partial", "blocked", "failed"), default="success"); deliver.set_defaults(func=cmd_deliver)
    decide = sub.add_parser("decide"); decide.add_argument("--root", required=True); decide.add_argument("--task-id", required=True); decide.add_argument("--decision", choices=("accepted", "rework", "canceled"), required=True); decide.set_defaults(func=cmd_decide)
    revise = sub.add_parser("revise"); revise.add_argument("--root", required=True); revise.add_argument("--task-id", required=True); revise.set_defaults(func=cmd_revise)
    validate = sub.add_parser("validate"); validate.add_argument("--root", required=True); validate.set_defaults(func=cmd_validate)
    return top


if __name__ == "__main__":
    arguments = parser().parse_args()
    arguments.func(arguments)
