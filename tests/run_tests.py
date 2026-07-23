#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "skills" / "project-main-thread" / "scripts" / "bootstrap_project.py"
TASKCTL = ROOT / "skills" / "project-task-handoff" / "scripts" / "taskctl.py"


def run(*args: str, ok: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run([sys.executable, *args], text=True, encoding="utf-8", capture_output=True)
    if ok and result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)
    if not ok and result.returncode == 0:
        raise AssertionError("Command unexpectedly succeeded")
    return result


def payload(result: subprocess.CompletedProcess[str]) -> dict:
    return json.loads(result.stdout)


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="codex-workflow-test-") as temp:
        project = Path(temp) / "demo"
        first = payload(run(str(BOOTSTRAP), "--root", str(project), "--mode", "auto", "--project-name", "Demo", "--background", "Workflow test"))
        assert first["mode"] == "bootstrap"
        start_before = (project / "00_Control" / "START_HERE.md").read_text(encoding="utf-8")
        second = payload(run(str(BOOTSTRAP), "--root", str(project), "--mode", "auto", "--project-name", "Changed"))
        assert second["mode"] == "resume"
        assert (project / "00_Control" / "START_HERE.md").read_text(encoding="utf-8") == start_before
        assert payload(run(str(BOOTSTRAP), "--root", str(project), "--mode", "takeover"))["mode"] == "takeover"

        one = payload(run(str(TASKCTL), "new", "--root", str(project), "--slug", "audit", "--objective", "Audit the result"))
        two = payload(run(str(TASKCTL), "new", "--root", str(project), "--slug", "tests", "--objective", "Run tests"))
        initial_state = json.loads((project / "00_Control" / "tasks" / one["task_id"] / "state.json").read_text(encoding="utf-8"))
        assert initial_state["task_status"] == "ready"
        assert initial_state["attempts"] == {}
        ambiguous = run(str(TASKCTL), "claim", "--root", str(project), ok=False)
        assert "found 2" in ambiguous.stderr

        claim = payload(run(str(TASKCTL), "claim", "--root", str(project), "--task-id", one["task_id"], "--thread-id", "worker-1"))
        assert claim["attempt_id"] == "A01"
        result = payload(run(str(TASKCTL), "result", "--root", str(project), "--task-id", one["task_id"], "--attempt-id", "A01"))
        assert Path(result["result"]).exists()
        run(str(TASKCTL), "deliver", "--root", str(project), "--task-id", one["task_id"], "--attempt-id", "A01", "--status", "failed", "--outcome", "failed")
        failed_state = json.loads((project / "00_Control" / "tasks" / one["task_id"] / "state.json").read_text(encoding="utf-8"))
        assert failed_state["task_status"] == "ready"
        assert failed_state["attempts"]["A01"]["status"] == "failed"

        retry_after_failure = payload(run(str(TASKCTL), "claim", "--root", str(project), "--task-id", one["task_id"], "--thread-id", "worker-2"))
        assert retry_after_failure["attempt_id"] == "A02"
        run(str(TASKCTL), "result", "--root", str(project), "--task-id", one["task_id"], "--attempt-id", "A02")
        run(str(TASKCTL), "deliver", "--root", str(project), "--task-id", one["task_id"], "--attempt-id", "A02")
        run(str(TASKCTL), "decide", "--root", str(project), "--task-id", one["task_id"], "--decision", "accepted")

        revision = payload(run(str(TASKCTL), "revise", "--root", str(project), "--task-id", one["task_id"]))
        assert revision["revision"] == 2
        retry = payload(run(str(TASKCTL), "claim", "--root", str(project), "--task-id", one["task_id"], "--thread-id", "worker-2"))
        assert retry["attempt_id"] == "A03"
        assert retry["revision"] == 2

        main_skill = (ROOT / "skills" / "project-main-thread" / "SKILL.md").read_text(encoding="utf-8")
        handoff_skill = (ROOT / "skills" / "project-task-handoff" / "SKILL.md").read_text(encoding="utf-8")
        assert "`/root`" in main_skill and "not the Codex runtime role" in main_skill
        assert "Say \"thread created\" only after" in handoff_skill
        assert "Never impersonate the Worker" in handoff_skill

        run(str(TASKCTL), "validate", "--root", str(project))
        state = json.loads((project / "00_Control" / "tasks" / two["task_id"] / "state.json").read_text(encoding="utf-8"))
        assert state["task_status"] == "ready"

    print("All workflow tests passed.")


if __name__ == "__main__":
    main()
