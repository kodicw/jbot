# Future Questions & Ideas

- [x] **Multiple Agents:** Users can now run multiple agents simultaneously by defining them in `programs.jbot.agents`.
- [x] **Roles and Descriptions:** Agents can be assigned specific roles and descriptions (e.g., QA, CEO, Lead Developer) which are injected into their system prompt.
- [x] **Community/Company Structure:** Simulated by multi-agent coordination using shared memory logs, agent-specific queues, and role-based guidance in the prompt.
- [x] **Robust Coordination:** Added agent-specific memory queues and a consolidation lock to prevent race conditions in multi-agent environments.
- [x] **Task Board (Blackboard):** Explicitly implemented a `TASKS.md` manager that agents use to claim and update work status. Injected into the prompt for better coordination.
- **Script-Based Wrapper:** Should the entire execution loop be wrapped in a standalone script (e.g., using Nushell) that takes arguments for roles, directories, and descriptions? This would move logic out of the systemd unit and make it more portable and testable. (Partially addressed by multi-agent support; needs better coordination mechanisms).
- **Efficient Testing:** How can we make testing methods more efficient without needing a full QEMU VM? We should research using `pkgs.runCommand` for logic validation and `bubblewrap` direct execution for sandbox verification.