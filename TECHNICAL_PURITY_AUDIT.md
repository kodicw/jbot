# Technical Purity Audit - 2026-04-26

## 🚩 Critical Violations (DRY & Modularity)

1.  **Duplicate Code (DRY Violation)**:
    *   `get_recent_messages` is implemented identically in both `scripts/jbot_utils.py` and `scripts/jbot_infra.py`.
    *   `get_recent_messages` is called from `jbot_cli.py`, `jbot_utils.py`, and `jbot_agent.py`.

2.  **Circular Dependency**:
    *   `jbot_infra.py` imports `jbot_utils`.
    *   `jbot_utils.py`'s `generate_dashboard` function imports `jbot_infra` locally to avoid a circular import. This indicates that `generate_dashboard` (a high-level organizational task) is misplaced in a low-level utility module.

3.  **Inefficient Context Assembly**:
    *   In `jbot_cli.py`, the `get_status` function calls `tasks.parse_tasks()` twice unnecessarily, increasing the load on the `nb` knowledge base.

4.  **Tangled Responsibilities**:
    *   `jbot_utils.py` is currently a mix of low-level stable note updates and high-level markdown generation.
    *   `jbot_cli.py` contains significant business logic for version management and system prompt resolution that could be further modularized.

## 🛠️ Recommended Remediation Plan

1.  **Consolidate Messaging**:
    *   Move `get_recent_messages` to `jbot_core.py` (as it's a core filesystem/data retrieval task) or `jbot_infra.py` (and remove it from `jbot_utils.py`).
    
2.  **Refactor Dashboard Generation**:
    *   Move `generate_dashboard` from `jbot_utils.py` to `jbot_infra.py` or a dedicated `jbot_dashboard.py` module.
    
3.  **Optimize CLI**:
    *   Refactor `get_status` in `jbot_cli.py` to use a single `tasks_data` object.
    
4.  **Modularize Versioning**:
    *   Move `handle_version` logic from `jbot_cli.py` to a dedicated `jbot_version.py` or into `jbot_core.py`.

## 🤖 Agent Verification
*   Agents seem to be following their roles, but the underlying infrastructure they use is becoming "muddy". 
*   The `lead` agent should be tasked with this refactor to ensure the "hands of the project" are maintaining technical purity.
