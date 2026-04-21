# JBot Proposal 001: Stateless Agent Execution Model (SAEM)

**Status:** Draft
**Author:** Principal Architect (architect)
**Date:** 2026-04-21

## 1. Problem Statement
The current JBot execution model relies on agents modifying the project filesystem directly during their execution loop. While it claims to be "stateless," it is actually "in-place stateful," which leads to several architectural weaknesses:
*   **Atomicity Failure**: If an agent process is killed or fails halfway, the project is left in a partially modified, potentially broken state.
*   **Non-Reproducibility**: The context provided to the agent is constructed dynamically from the live filesystem. It is impossible to exactly reconstruct what an agent "saw" at time T without expensive snapshots.
*   **Race Conditions**: Multiple agents (if scheduled concurrently) can conflict on the same files without a coordination layer.
*   **Verification Lag**: Verification (pre-commit checks) happens *after* the files have already been modified, requiring a manual or complex "rollback" on failure.

## 2. Proposed Solution: JBot-SAEM
We propose transitioning to a truly stateless execution model where agents operate on immutable inputs and produce explicit, verifiable outputs before any state change is committed.

### 2.1 Core Components
1.  **Context Snapshotting**: Before an agent runs, the system generates a signed, immutable context bundle (JSON) containing everything the agent needs to know (Goal, Tasks, Memory, relevant File Content).
2.  **Overlay Workspace**: Agents execute inside a temporary, isolated workspace (e.g., a `tmpfs` or an `overlayfs`). The main project directory is mounted **READ-ONLY**.
3.  **Transactional Commits**: After execution, the agent's changes are extracted as a `git diff` (or a set of filesystem operations).
4.  **Pre-Commit Validation**: The extracted changes are validated against the project's test suite and architectural rules *within the isolated workspace*.
5.  **Atomic Application**: Only if validation passes are the changes applied to the main project directory.

### 2.2 Operational Flow
1.  **MANAGER** (Systemd/Launcher):
    *   Creates a `tmpfs` workspace.
    *   Mounts the Project Root as **read-only** into the workspace.
    *   Mounts a writable layer for the agent's specific output.
2.  **AGENT RUNNER** (`jbot-agent.py`):
    *   Assembles the context bundle.
    *   Invokes Gemini CLI pointing to the writable workspace layer.
    *   Upon completion, captures the diff between the base (read-only) and the workspace.
3.  **VERIFIER**:
    *   Runs `nix flake check` or `pytest` on the workspace.
    *   If SUCCESS: Commits the diff to the Project Root.
    *   If FAILURE: Discards the workspace and logs the error.

## 3. Benefits
*   **Architectural Purity**: Adheres to the stateless principles of functional programming and Nix.
*   **Robustness**: Zero risk of partial/broken commits.
*   **Auditability**: The exact `context.json` and `diff.patch` for every agent run can be archived for audit or debugging.
*   **Scalability**: Allows for safe concurrent agent execution without locking the entire project directory.

## 4. Implementation Plan
1.  **Phase 1 (Research)**: Verify `bubblewrap` and `overlayfs` compatibility in the current NixOS/VM environment.
2.  **Phase 2 (Utilities)**: Update `jbot_utils.py` to include context bundling and diff extraction logic.
3.  **Phase 3 (Runner)**: Refactor `jbot-agent.py` to implement the Transactional Loop.
4.  **Phase 4 (Nix)**: Update `jbot.nix` to configure the read-only mounts and workspace provisioning.

## 5. Success Metrics
*   100% atomic commits (verified by observing no partial changes on agent failure).
*   Zero manual rollbacks required for failed agent runs.
*   Ability to re-run an agent with an archived `context.json` and get consistent output.
