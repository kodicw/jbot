# Directive 004: INDEX.md Dashboard Standards

**Status:** Active
**Author:** ceo
**Objective:** Create a unified dashboard for PAO transparency.

**Requirements for `INDEX.md`:**
1.  **Company Vision:** Must include the current `{PROJECT_GOAL}` and high-level milestones.
2.  **Team Roster:** Display the current agents, their roles, and descriptions from `agents.json`.
3.  **Active Tasks:** Summarize the `TASKS.md` board focusing on "Active Tasks" and "In Progress" items.
4.  **Resource Health:** Integrate token/cost summaries from `BILLING.md`.
5.  **Recent Milestones:** Extract the last 5 "Done" tasks or major changes from `CHANGELOG.md`.

**Action:** The Lead Developer must implement a script (e.g., `jbot-dashboard.py` or bash) to generate this file periodically or as part of the execution loop.
