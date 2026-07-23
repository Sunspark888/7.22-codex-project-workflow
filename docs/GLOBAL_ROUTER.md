# Global AGENTS.md router

Keep this router short. Skills and project files own the details.

```markdown
## Long-running project workflow routing

- When the user says this is a new project and appoints the current agent as the main thread/process, use `project-main-thread` to bootstrap the project control layer.
- When the user asks to resume or take over a long-running project, use `project-main-thread` and start from `00_Control/START_HERE.md`.
- When the user requests an independent worker/child thread or asks a worker to return to the main thread, use `project-task-handoff`.
- Prefer direct work, then native subagents, then independent file-based workers. Do not store project-specific state in this global file.
- Explicit Worker/child-process intent takes precedence over generic project resume. The Codex runtime label `/root` means root of the current thread, not project main.
- Never claim that an independent thread was created unless a thread-creation tool returned success. A task card alone is only a ready assignment.
```
