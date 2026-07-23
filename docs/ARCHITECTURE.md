# Architecture and flows

## Three execution paths

```mermaid
flowchart TD
    A["Main agent receives work"] --> B{"Short or tightly coupled?"}
    B -->|Yes| C["Main agent executes"]
    B -->|No| D{"Parallel and native subagent fits?"}
    D -->|Yes| E["Native subagent"]
    E --> F["Automatic summary return"]
    D -->|No| G{"Long, result-oriented, recoverable?"}
    G -->|Yes| H["Independent Worker"]
    H --> I["Task card and result card"]
    G -->|No| C
    F --> J["Main agent reviews"]
    I --> J
```

## New project and takeover

```mermaid
flowchart LR
    U["User: this is a new project; you are the main thread"] --> M["project-main-thread"]
    M --> Q{"START_HERE exists?"}
    Q -->|No| B["bootstrap"]
    Q -->|Yes, same main| R["resume"]
    Q -->|Yes, new main| T["takeover"]
    B --> S["AGENTS + START_HERE + Ledger + Decision Log"]
    R --> S
    T --> S
```

## Independent Worker handoff

```mermaid
sequenceDiagram
    participant U as User
    participant M as Main agent
    participant F as Project files
    participant W as Independent Worker
    U->>M: Give this long result-only task to a worker
    M->>F: Create task ID and revisioned task contract
    M-->>W: Optional automatic thread creation or Worker Prompt
    W->>F: Create attempt claim
    W->>W: Execute only allowed scope
    W->>F: Write one result card and deliver
    W-->>M: Optional notification
    M->>F: Read result card and verify
    M->>F: Accept, rework, or cancel; update Ledger if needed
```

An independent top-level Codex thread may label its local agent `/root`. That is a runtime-local label, not the project role. Worker identity comes from the explicit launch prompt or assigned task card. The main agent may report a new thread only after a client thread-creation operation succeeds; a task card by itself remains a ready assignment.

## Facts and authority

```mermaid
flowchart TD
    A["AGENTS.md behavior rules"] --> B["START_HERE stable project map"]
    B --> C["PROJECT_LEDGER accepted current state"]
    B --> D["DECISION_LOG reasons"]
    B --> E["tasks revisioned contracts"]
    E --> F["claims execution identity"]
    F --> G["results execution evidence"]
    G --> C
```

## Why this is deliberately small

The files act like a durable mailbox and checkpoint layer. This is enough for a personal local workflow. A database or queue becomes useful only when many autonomous workers must coordinate continuously; adding one here would increase operational cost without solving the primary problem, which is main-thread context quality.
