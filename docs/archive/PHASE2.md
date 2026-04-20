# Proposal: Phase 2 - Professional Autonomous Organization (PAO)

Following the successful implementation of the basic multi-agent infrastructure, Phase 2 focuses on operational excellence, transparency, and strategic steering.

## 1. Dynamic Goal Steering
The CEO agent should be the "Master of the Goal".
- **Mechanism:** The `{PROJECT_GOAL}` injection currently defaults to a static string. We will formalize `.project_goal` as the source of truth.
- **Action:** The CEO agent will periodically review `TASKS.md` and the Shared History to update `.project_goal` with high-level priorities for the next cycle.

## 2. Formal Directives
Agents currently coordinate via `TASKS.md`. However, urgent architectural changes or pivots need a more assertive mechanism.
- **Mechanism:** A `.jbot/directives/` directory.
- **Rules:** Directives are injected into the prompt with higher precedence than general tasks. Only "Lead" or "CEO" agents can issue/remove directives.


## 4. Human-in-the-Loop (Gatekeeping)
For sensitive changes (e.g., updating `jbot.nix` or deleting files), we need a "Proposal" flow.
- **Mechanism:** Introduce an `In Review (Human)` state in `TASKS.md`.
- **Constraint:** Agents are forbidden from executing the final step of a task in this state until a human moves it to `Approved`.

## 5. Visual Dashboard (`INDEX.md`)
To make the project state accessible at a glance.
- **Mechanism:** A lightweight script that parses `TASKS.md`, `memory.log`, and `agents.json` to generate a human-friendly `INDEX.md`.
- **Content:** Team roster, Active tasks, Recent milestones, and "Company Health" metrics.
