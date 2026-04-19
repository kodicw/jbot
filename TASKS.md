# JBot Task Board

## Strategic Vision (CEO)
The goal for Phase 2 is to transform JBot from a multi-agent script into a **Professional Autonomous Organization (PAO)**. This involves better steering, cost transparency, and human-in-the-loop coordination.

## Active Tasks
- [ ] Add NixOS tests for multi-agent task handover (Agent: Lead Developer) - Status: In Progress
- [x] Implement Dynamic Goal Steering (Agent: ceo) - Status: Done (Updated .project_goal for Phase 2)

## Backlog (Phase 2)
- [ ] Implement Formal Directives system (Agent: Lead Developer)
- [ ] Add Token/Cost tracking to `jbot-agent.py` and `BILLING.md`
- [ ] Create `INDEX.md` dashboard generator script
- [ ] Add "Proposal" state to Task State Machine (Human-in-the-loop)
- [ ] Support nested sub-projects and agents.json filtering

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
