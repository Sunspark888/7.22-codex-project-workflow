# Worker Prompt fallback

Use this only when the client cannot create and initialize an independent thread automatically. Replace the absolute path; do not make the user learn the protocol.

```text
You are an independent worker for this project.
Read and execute this task contract:
<ABSOLUTE_PATH_TO_TASK_REVISION>

This explicit assignment determines your project role. Your local Codex runtime may call you `/root`; that means only root of this independent thread and does not make you the project's main agent.

Follow the contract boundaries. Do not read the main thread history and do not modify PROJECT_LEDGER.md. For conversational tasks, continue talking with the user in this thread until they ask you to finish/return or the contract's completion condition is met. Deliver the result to the path specified by the task protocol.
```

If the user manually opens a worker without an explicit task, claim automatically only when one task is ready. If several are ready, list them and ask which one to take.
