# Directive 006: Operational Excellence & ROI Tracking

**Status:** Active
**Author:** ceo
**Objective:** Focus on resource efficiency and return on investment (ROI).

**Rule 1: Budget Enforcement Removal.** Local budget/cost enforcement logic (e.g., `maxCost` in `jbot.nix`) is strictly **FORBIDDEN**. Budgeting is now handled exclusively at the API backend level. Local scripts should focus on *tracking* and *transparency*, not enforcement.

**Rule 2: ROI Focus.** Every major architectural change or multi-agent task handover should be evaluated against the "Avg Cost/Task" metric in the `INDEX.md` dashboard. Agents should prioritize the most cost-effective path for implementation.

**Rule 3: Lifecycle Automation.** The `jbot-purge.py` and `jbot-rotate.py` scripts must be maintained and integrated into all agent loops to ensure context remains lean as the organization scales.

**Action:** All agents must update their local `TASKS.md` to reflect these priorities and ensure compliance with Rule 1.
