# Proposal: Multi-Agent Community/Company Architecture

To support complex organizational structures (e.g., QA, CEO, Lead Developer) and large-scale autonomous communities, JBot needs a robust coordination mechanism.

## 1. Agent-Specific Memory & Queues
Currently, agents share a single `.memory_queue.json`, leading to race conditions.
**Proposed Change:** Use `.jbot/queues/${agent_name}.json` for temporary output and `.jbot/memory.log` for shared history.

## 2. Shared vs. Private Context
Agents should be able to distinguish between their own previous thoughts and the actions of others.
**Proposed Change:** Format shared memory entries as `[Agent: Role] Summary`. Inject both a "Personal Memory" (filtered history) and "Shared History" (all agents) into the prompt.

## 3. Task Management (The "Blackboard")
A "Company" needs a central place to track work.
**Proposed Change:** Introduce a `TASKS.md` (or `TASKS.json`) file that acts as the "Source of Truth" for coordination.
- **CEO/Lead**: Can add/remove/assign tasks.
- **Developer**: Can pick up tasks and update status to "In Progress" or "Done".
- **QA**: Can verify tasks and move them to "Closed" or "Reopened".

## 4. Hierarchy & Dependencies
Some agents should run after others.
**Proposed Change:** Add a `dependsOn` option to `programs.jbot.agents`. This will map to systemd `After=` and `Wants=` dependencies.

## 5. Role-Specific Capabilities
A "CEO" might need `gh` (GitHub CLI) access to manage PRs, while a "Developer" might only need `git`.
**Proposed Change:** Add an `extraPackages` option per agent to customize their sandbox environment.

## 6. Centralized Loop Script
Move the execution logic from `jbot.nix` into a dedicated Python or Bash script (e.g., `jbot-loop`) for better maintainability and testing.
