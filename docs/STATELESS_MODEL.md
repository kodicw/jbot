# JBot Stateless Agent Execution Model (Architectural Proposal)

## 1. Objective
To achieve architectural purity by decoupling the AI agent's core reasoning (Intelligence) from the infrastructure's state management (Maintenance).

## 2. Current State (Stateful/Coupled)
- `jbot-agent.py` is responsible for its own context assembly AND for managing the state of the entire system (rotation, purging, consolidation).
- Agents compete for locks on `memory.log` and `.jbot/rotation.lock`.
- Failures in maintenance scripts can block agent execution.
- High architectural coupling between the reasoning loop and the filesystem maintenance logic.

## 3. Proposed Model: Stateless Intelligence
The agent execution loop will be transitioned to a strictly **stateless** model where each run is an isolated, side-effect-free (excluding its specific output) transformation of context into action.

### 3.1. Stateless Runner (`jbot-agent.py`)
- **Action**: Limited to `Context Assembly` -> `LLM Invocation` -> `Output Memory Queue`.
- **Removal**: All calls to `jbot-purge.py`, `jbot-rotate.py`, `jbot-rotate-tasks.py`, `jbot-rotate-messages.py`, and manual queue consolidation.
- **Verification**: Post-execution hooks (like `pre-commit`) are retained as they verify the *output* of the agent, not the *state* of the infrastructure.

### 3.2. State Management Service (`jbot-maintenance`)
- **Action**: A dedicated, periodic systemd service/timer that handles all cross-agent state operations.
- **Responsibilities**:
    - Memory Queue Consolidation (merging `.jbot/queues/*.json` into `.jbot/memory.log`).
    - Log Rotation & Expired Directive Purging.
    - Global Dashboard Generation (`INDEX.md`).
    - Task Board Rotation (`TASKS.md`).

### 3.3. Architecture Comparison
| Feature | Current Model | Stateless Model |
| :--- | :--- | :--- |
| **Memory Management** | Distributed (Agents consolidate) | Centralized (Maintenance Service) |
| **Concurrency** | Locking required (Complex) | Lock-free (Stateless agents) |
| **Failure Isolation** | Maintenance failure = Agent failure | Independent failures |
| **Scalability** | Limited by lock contention | Theoretically infinite parallel agents |

## 4. Implementation Plan
1. **Refactor `jbot-agent.py`**: Strip all maintenance logic.
2. **Refactor `jbot.nix`**: 
    - Add a `jbot-maintenance` service and timer.
    - Ensure `jbot-agent` services depend on the presence of necessary state but don't manage it.
3. **Refactor `scripts/jbot_utils.py`**: Ensure utilities support the new separated responsibilities.
4. **Verification**: 
    - Update `tests/unit-test.nix` and other tests to verify the separation.
    - Ensure `jbot-agent` can run even if `jbot-maintenance` has not run yet (robustness).

## 5. Architectural Mandate
Agents MUST NOT modify infrastructure state files (like `memory.log` or `agents.json`) directly. They interact with state only through well-defined input context and output queues.
