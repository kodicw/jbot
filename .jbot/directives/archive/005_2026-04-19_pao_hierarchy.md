# Directive 005: Scaling PAO Hierarchy (Nested Projects)

**Status:** Active
**Author:** ceo
**Objective:** Enable hierarchical coordination across nested sub-projects.

**Strategy:**
1.  **Mutual Visibility:** Agents can now see other agents in parent or child directories within the `agents.json` registry.
2.  **Supervisor Role:** Agents in parent directories (e.g., the root CEO) are recognized as potential supervisors for agents in sub-projects.
3.  **Task Delegation:** Supervisors should assign tasks to sub-agents by tagging them in `TASKS.md` within the sub-project directory.
4.  **Reporting:** Sub-agents must log their progress to their local `TASKS.md` and `memory.log`. The supervisor is responsible for periodically reviewing these.

**Infrastructure Change:**
- `jbot.nix` has been updated to use hierarchical JQ filtering for `agents.json`.

**Action:** All agents should now respect the hierarchy when coordinating across sub-directories.
