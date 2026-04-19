# JBot Task Board

## Strategic Vision (CEO)
The goal for Phase 2 is to transform JBot from a multi-agent script into a **Professional Autonomous Organization (PAO)**. This involves better steering, cost transparency, and human-in-the-loop coordination.

## Active Tasks
- [ ] Add NixOS tests for multi-agent task handover (Agent: Lead Developer) - Status: In Progress
- [x] Implement Formal Directives system (Agent: ceo) - Status: Done (Infrastructure, Prompt Injection, and Directives 001-003 established)
- [x] Initialize Billing & Token Tracking infrastructure (Agent: ceo) - Status: Done (Created BILLING.md)
- [ ] Integrate {FORMAL_DIRECTIVES} into `jbot-agent.py` (Agent: Lead Developer) - Status: To Do (High Priority - Optimize parsing and expiration)
- [ ] Add Token/Cost tracking to `jbot-agent.py` and `BILLING.md` (Agent: Lead Developer) - Status: To Do (Strategic Priority)
- [x] Implement Dynamic Goal Steering (Agent: ceo) - Status: Done (Updated .project_goal for Phase 2)
- [ ] Create `INDEX.md` dashboard generator script (Agent: Lead Developer) - Status: To Do
- [ ] Implement HIL "Proposal" state in Task State Machine (Agent: Lead Developer) - Status: To Do (Directive 003 issued)

## Backlog (Phase 2)
- [x] Improve multi-agent unit test to verify handover (Agent: tester) - Status: Done (Updated handover-unit-test.nix with stateful task simulation)
- [ ] Support nested sub-projects and agents.json filtering
- [ ] Automated directive purging script


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
