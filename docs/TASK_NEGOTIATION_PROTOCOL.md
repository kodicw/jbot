# JBot Task Negotiation & Prioritization Protocol (TNPP)

This document defines the decentralized protocol for agent-to-agent coordination regarding task assignment and prioritization within the JBot Flat Organization.

## 1. Task Lifecycle States

Tasks in `TASKS.md` follow these states:
- **Backlog**: Identified tasks that are not yet prioritized for immediate action.
- **Proposal**: Complex architectural changes requiring a research phase before implementation.
- **Active Tasks**: Tasks currently being worked on.
- **In Review**: Tasks waiting for verification (by a Peer or Human).
- **Done**: Verified and completed tasks.

## 2. Negotiation Messages

Agents communicate via `.jbot/messages/` using structured subjects to facilitate negotiation.

### 2.1 Task Proposal
- **Action**: Proposing a new task.
- **Message Subject**: `PROPOSAL: [Short Task Description]`
- **Content**: Reasoning, dependencies, and suggested assignee (optional).
- **Effect**: If no objections are raised, the proposer or suggested agent adds the task to the `Backlog` in `TASKS.md`.

### 2.2 Task Claiming
- **Action**: An agent wants to take responsibility for a task in the `Backlog`.
- **Message Subject**: `CLAIM: [Task Description]`
- **Effect**: The agent moves the task to `Active Tasks` in `TASKS.md` and assigns themselves `(Agent: Name)`.

### 2.3 Task Delegation
- **Action**: Requesting another agent to take a task.
- **Message Subject**: `DELEGATE: [Task Description] to [Target Agent]`
- **Content**: Why the target agent is better suited.
- **Acknowledgment**: The target agent must reply with `ACCEPT: [Task Description]` before updating `TASKS.md`.

### 2.4 Priority Negotiation
- **Action**: Suggesting a change in the order of `Active Tasks` or `Backlog`.
- **Message Subject**: `PRIORITY: [Task A] > [Task B]`
- **Reasoning**: Technical dependencies, urgency, or resource optimization.

## 3. Conflict Resolution

1. **Double-Claim**: If two agents claim the same task in the same cycle, they must negotiate in the next cycle. If no agreement is reached, the **Lead Developer** (lead) has final authority.
2. **Stalled Tasks**: If an `Active Task` has no progress for 3 cycles, any agent can send a `QUERY: [Task Description]` message.
3. **Objections**: Any agent can object to a `PROPOSAL` or `PRIORITY` shift by sending an `OBJECTION: [Reason]`.

## 4. Technical Excellence Mandate

- All negotiations must prioritize **Architectural Purity** and **Code Robustness**.
- Tasks that increase technical debt must be identified and countered with "Refactor" tasks in the `Backlog`.
- 100% test coverage is a prerequisite for moving any task from `In Review` to `Done`.

## 5. Implementation Rules

- Agents MUST NOT modify `TASKS.md` for another agent's assigned tasks without explicit `DELEGATE` and `ACCEPT` messages.
- Agents SHOULD update the `Backlog` as soon as a `PROPOSAL` is accepted by the community (silence is often consent if no objections within 1 cycle).
