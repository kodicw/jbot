# Proposal: Refined Stateless Agent Execution Model (v2)

## 1. Objective
To enforce the "Stateless Intelligence" model at the infrastructure level, ensuring agents cannot inadvertently or maliciously corrupt global infrastructure state (like the shared memory log).

## 2. Refined Rules
1. **Immutable Infrastructure Context**: Agents receive `memory.log` and `agents.json` as read-only files.
2. **Directed Output**: Agents write their reflection/memory ONLY to a dedicated queue file in `.jbot/queues/{AGENT_NAME}.json`.
3. **State Management Isolation**: Only the `jbot-maintenance` service has write access to `memory.log` and is responsible for directory initialization.
4. **Project State vs. Infra State**: Agents retain write access to "Project State" (codebase, `TASKS.md`, `.jbot/messages/`, `.jbot/directives/`) as these are necessary for development and coordination.

## 3. Implementation Plan

### 3.1. Infrastructure Initialization (`jbot-maintenance.py`)
- The maintenance script will be responsible for creating all required `.jbot/` subdirectories.
- This ensures that agents running in a restricted sandbox don't fail when attempting to create directories they shouldn't manage.

### 3.2. Restricted Sandbox (`jbot.nix`)
- Update the `bwrap` configuration to:
    - Bind `.jbot/memory.log` as read-only (`--ro-bind-try`).
    - Bind `.jbot/agents.json` as read-only (`--ro-bind-try`).
    - Ensure `.jbot/queues/` is writable.

### 3.3. Robust Agent Runner (`jbot-agent.py`)
- Remove directory creation logic (or make it strictly non-fatal if it fails).
- Ensure it handles missing `memory.log` gracefully (statelessness implies it can run even if history is empty).

## 4. Architectural Benefits
- **Integrity**: Agents cannot overwrite or delete the shared memory log.
- **Simplicity**: The division of labor between "Reasoning" (Agent) and "Maintenance" (Service) is absolute.
- **Security**: Reduces the blast radius of an agent run.

## 5. Verification Plan
- **Unit Tests**: Update `tests/test_agent.py` to verify it handles read-only infrastructure.
- **System Tests**: Verify that `jbot-maintenance` correctly initializes the environment.
- **Coverage**: Ensure 100% coverage of the new isolation logic.
