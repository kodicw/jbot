# JBot Governance & Coordination

This document defines the organizational structure and coordination protocols for the JBot project.

## 1. Organizational Model: Flat Organization

JBot follows a **Flat Organization** model focused on **Technical Excellence**.

- **Internal Cohesion**: All JBot components (agents, infrastructure, scripts) for a single organization MUST reside under a single Linux user account.
- **External Isolation**: Management of entirely different projects/organizations is handled exclusively by NixOS/Home Manager using separate user accounts.
- **No Internal Hierarchy**: There are no "sub-projects" or "nested organizations". Coordination is achieved through shared state and decentralized negotiation.

## 2. Team Roles

| Role | Agent | Responsibility |
|------|-------|----------------|
| **Technical Founder (CEO)** | `ceo` | Set vision, prioritize the roadmap, and ensure long-term architectural alignment. |
| **Principal Architect** | `architect` | Critique architectural decisions, advocate for simplicity, and maintain standards. |
| **Lead Developer** | `lead` | Manage core infrastructure, implement features, and coordinate releases. |
| **QA Engineer** | `tester` | Verify changes, achieve 100% test coverage, and report regressions. |

## 3. Coordination Protocols

### 3.1 Task Board (TASKS.md)
The `TASKS.md` file serves as the centralized "Blackboard" for the organization. All agents MUST respect the task lifecycle:
1. **Backlog**: Unassigned ideas or future work.
2. **Proposal**: Complex changes requiring a research/design phase.
3. **Active Tasks**: Work currently in progress, assigned to an agent.
4. **In Review**: Completed work waiting for verification (Human or Peer).
5. **Done**: Verified and completed work.

### 3.2 Task Negotiation & Prioritization Protocol (TNPP)
Agents coordinate via `.jbot/messages/` using structured subjects:
- `PROPOSAL`: Suggesting a new task or architectural change.
- `CLAIM`: Taking responsibility for a task.
- `DELEGATE`: Requesting another agent to handle a task.
- `PRIORITY`: Negotiating the order of tasks.

See [docs/TASK_NEGOTIATION_PROTOCOL.md](./docs/TASK_NEGOTIATION_PROTOCOL.md) for full details.

## 4. Engineering Standards

- **Architectural Purity**: Prioritize elegant abstractions and simplicity over "clever" hacks.
- **Self-Documenting Code**: Code must be expressive and clear. Favor meaningful naming and modular design.
- **Exhaustive Verification**: 100% test coverage for all core components is a prerequisite for a v1.0.0 release.
- **Stateless Agent Model**: Agents operate in a restricted, stateless environment. Infrastructure maintenance is handled by centralized service scripts.
