# Future Questions & Ideas

- [x] **Multiple Agents:** Users can now run multiple agents simultaneously by defining them in `programs.jbot.agents`.
- [x] **Roles and Descriptions:** Agents can be assigned specific roles and descriptions (e.g., QA, CEO, Lead Developer) which are injected into their system prompt.
- [x] **Community/Company Structure:** Simulated by multi-agent coordination using shared memory logs, agent-specific queues, and role-based guidance in the prompt.
- [x] **Robust Coordination:** Added agent-specific memory queues and a consolidation lock to prevent race conditions in multi-agent environments.
- [x] **Task Board (Blackboard):** Explicitly implemented a `TASKS.md` manager that agents use to claim and update work status. Injected into the prompt for better coordination.
- [x] **Script-Based Wrapper:** Extracted the entire execution loop into `jbot-agent.py`. This moves logic out of the systemd unit and makes it more portable and testable.
- [x] Agent Registry: A `.jbot/agents.json` file is now generated and injected, allowing agents to know their teammates' roles. Now project-scoped for better isolation.
- [x] Direct Messaging: Agents can now communicate via `.jbot/messages/` for asynchronous coordination.
- [x] Hierarchical Coordination: Implemented via `supervisor` option in `jbot.nix` and hierarchical rules in `jbot_prompt.txt`. "Lead" and "CEO" roles have architectural authority.
- [x] Research and implement efficient non-VM testing (using `runCommand`) (Agent: Lead Developer)

## Phase 2: Professional Autonomous Organization (PAO)

- **Dynamic Goal Steering:** The CEO agent should be able to update the `.project_goal` file to shift focus based on progress.
- **Formal Directives:** A system for "Pinning" messages as high-priority directives that all agents must follow until rescinded.
- **Resource/Cost Tracking:** Agents should log their estimated token usage to a shared `BILLING.md` or similar to track operational costs.
- **Sub-Project Isolation:** Support for nested `agents.json` or sub-directories for large monorepos where different teams work on different components.
- **Human-in-the-loop Gatekeeping:** A "Proposal" state for tasks where a human (or CEO) must approve a change before execution.
- **Self-Healing Infrastructure:** Agents should be able to propose updates to `jbot.nix` itself if they find a bottleneck in their sandbox.
- **Dashboarding:** Generate a static `INDEX.md` or HTML dashboard showing the current state of the "Company", recent tasks, and agent health.