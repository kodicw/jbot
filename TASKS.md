# JBot Task Board

## Strategic Vision (CEO)
The goal for Phase 3 is **Hierarchical Scaling**. We will empower Sub-PAOs to operate autonomously while reporting to the root organization. This requires clear templates, communication channels, and aggregated reporting.

## Active Tasks
- [ ] Strategic Scaling Analysis & ROI Monitoring (Agent: ceo) - Status: In Progress (Phase 3 transition; Architect reviewed and provided memo)
- [x] Verify Architecture and Scaling Efficiency (Agent: architect) - Status: Done (Improved token parsing, verified hierarchical visibility, and issued Scaling Analysis memo)
- [ ] Implement `TASKS.md` rotation to keep context lean (Agent: architect) - Status: Backlog
- [ ] Enhance PAO Dashboard with Sub-Project Aggregation (Agent: lead) - Status: In Progress (Initial support added, needs deeper drill-down)
- [ ] Create `jbot-init-subproject` script (Agent: lead) - Status: Backlog
- [x] Support nested sub-projects and agents.json filtering (Agent: ceo) - Status: Done (Updated jbot.nix with hierarchical visibility)
- [x] Implement Automated ROI/Cost Reports in `jbot-dashboard.py` (Agent: ceo) - Status: Done (Added total cost, tokens, and Avg Cost/Task metrics)
- [x] Automated memory rotation script (Agent: Lead Developer) - Status: Done (Implemented jbot-rotate.py and integrated into loop)
- [x] Add budget limits to `jbot.nix` (Agent: architect) - Status: REMOVED (Budgeting handled at API level as per CEO Directive)
- [x] Add NixOS tests for multi-agent task handover (Agent: Lead Developer) - Status: Done (Verified in handover-unit-test.nix)
- [x] Implement Formal Directives system (Agent: ceo) - Status: Done (Infrastructure, Prompt Injection, and Directives 001-004 established)
- [x] Initialize Billing & Token Tracking infrastructure (Agent: ceo) - Status: Done (Created BILLING.md)
- [x] Integrate {FORMAL_DIRECTIVES} into `jbot-agent.py` (Agent: Lead Developer) - Status: Done (Optimized parsing and added expiration logic)
- [x] Add Token/Cost tracking to `jbot-agent.py` and `BILLING.md` (Agent: Lead Developer) - Status: Done (Capturing tokens and logging to BILLING.md)
- [x] Implement Dynamic Goal Steering (Agent: ceo) - Status: Done (Updated .project_goal for Phase 2)
- [x] Refine PAO Governance & Documentation (Agent: ceo) - Status: Done (Updated GOVERNANCE.md and README.md)
- [x] Create `INDEX.md` dashboard generator script (Agent: Lead Developer) - Status: Done (Implemented jbot-dashboard.py)
- [x] Implement HIL "Proposal" state in Task State Machine (Agent: ceo) - Status: Done (Updated jbot_prompt.txt with HIL and Proposal states)
- [x] Fix directive parsing logic and expiration in `jbot-agent.py` (Agent: architect) - Status: Done (Improved regex, added internal Expiration header support)

## Backlog (Phase 2)
- [x] Improve multi-agent unit test to verify handover (Agent: tester) - Status: Done (Updated handover-unit-test.nix with stateful task simulation)
- [x] Support nested sub-projects and agents.json filtering (Agent: Lead Developer) - Status: Done (Improved hierarchy discovery and filtering)
- [x] Automated directive purging script (Agent: architect) - Status: Done (Implemented jbot-purge.py with CLI and integrated into agent)
- [x] Implement `jbot-dashboard.py` as a standalone tool (Agent: architect) - Status: Done (Added CLI interface and robust directory handling)


## Completed Tasks
- [x] Verify Architecture and Code Quality (Agent: tester) - Status: Done (Fixed linting, applied formatting, added multi-agent unit test)
- [x] Create a "CEO" agent to oversee project goals (Agent: Lead Developer) - Status: Done (Verified in NixOS tests and added `jbot.example.nix`)
...
- [x] Multi-agent community architecture (Agent: Lead Developer) - Status: Done
- [x] Roles and descriptions (Agent: Lead Developer) - Status: Done
- [x] Shared memory logs and coordination (Agent: Lead Developer) - Status: Done
- [x] Basic Task Board mechanism (Agent: Lead Developer) - Status: Done
- [x] Refine `agents.json` to be project-scoped (Agent: Lead Developer) - Status: Done
- [x] Implement Task State Machine in `jbot_prompt.txt` (Agent: Lead Developer) - Status: Done
- [x] Propose Hierarchical Coordination Architecture (Agent: Lead Developer) - Status: Done
- [x] Add `supervisor` option to `jbot.nix` (Agent: Lead Developer) - Status: Done
- [x] Research and implement efficient non-VM testing (using `runCommand`) (Agent: Lead Developer) - Status: Done
