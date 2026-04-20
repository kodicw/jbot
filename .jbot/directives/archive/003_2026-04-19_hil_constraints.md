# Directive 003: Human-in-the-Loop Constraints

**Status:** Active
**Author:** ceo
**Objective:** Ensure sensitive changes are manually approved.

**Rule:** Agents are strictly **FORBIDDEN** from using file-mutating tools (e.g., `replace`, `write_file`) on files related to tasks currently in the `In Review (Human)` state. These tasks are reserved for human verification and approval only.
