# Professional Autonomous Organization (PAO) Governance

This document outlines the decision-making process for JBot as a Professional Autonomous Organization.

## PAO Vision
JBot operates as a decentralized, multi-agent entity focused on infrastructure automation. We prioritize operational transparency, strategic steering, and human-in-the-loop coordination.

## Core Architectural Requirements

1. **Multi-User Project Isolation:** To ensure hardware-level security and clear organizational boundaries, entirely different projects MUST be separated using dedicated Linux user accounts via NixOS/Home Manager (e.g., Project A runs under User A, Project B runs under User B). However, all internal components and sub-projects of a single cohesive organization (like JBot) should remain under the same user to maintain architectural integrity and simplify coordination.
2. **Reproducibility:** All agent environments must be defined declaratively in Nix.
3. **Sandboxing:** agents must always run within a `bubblewrap` container, even when running under a dedicated user.
## Roles & Responsibilities

### Technical Founder (CEO)
- **Vision:** Sets the high-level product vision and long-term goals.
- **Steering:** Issues Formal Directives and updates the `.project_goal`.
- **Roadmap:** Prioritizes the `TASKS.md` board.

### Principal Architect
- **Critique:** Reviews architectural decisions and advocates for simplicity.
- **Standards:** Defines engineering standards and core infrastructure patterns.

### Lead Developer
- **Execution:** Manages the core JBot infrastructure and implements key features.
- **Coordination:** Oversees task handover and agent synchronization.

### QA Engineer (Tester)
- **Verification:** Runs tests, reports regressions, and ensures code quality.
- **Validation:** Verifies that architectural changes meet the defined criteria.

## Decision Process

### Strategic Steering (Directives)
The CEO and Lead Developer can issue **Formal Directives** via `.jbot/directives/`. These carry maximum precedence in agent prompts.
- Directives follow the `NNN_YYYY-MM-DD_Topic.md` naming convention.
- Directives automatically expire or are purged to prevent "Directive Bloat".

### Task State Machine
Agents use `TASKS.md` for coordination. Tasks follow a lifecycle:
`Backlog` -> `To Do` -> `In Progress` -> `In Review (Human)` -> `Done`.

### Human-in-the-Loop (HIL)
Tasks marked `In Review (Human)` require manual approval before final implementation. Agents are forbidden from modifying critical infrastructure files while a task is in this state.

## Resource Management
Token usage and estimated costs are tracked in `BILLING.md`. The PAO strives for cost-efficiency and transparent resource allocation.
