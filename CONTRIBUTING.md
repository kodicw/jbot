# Contributing Guide: JBot Engineering Standards

**Project:** JBot  
**Status:** Flat Multi-Agent Organization  
**Stack:** Nix (Flakes, Home Manager), Python 3, Systemd

---

## 1. Architectural Philosophy: Flat Organization

JBot follows a **Flat Organization** model. This means:
- **Internal Cohesion:** All components (agents, infra, scripts) live under a single Linux user account.
- **No Hierarchy:** We avoid nested project structures or "Sub-PAOs". Coordination happens via a shared `TASKS.md` and `.jbot/messages/`.
- **External Isolation:** Multi-project management is handled by creating *different* Linux users via NixOS/Home Manager.

---

## 2. Code Quality Standards

### Nix (Infrastructure & Configuration)
- **Formatting:** All `.nix` files must be formatted with `nixfmt` (RFC-style).
- **Linting:** Use `statix check` to identify anti-patterns.
- **Hermeticity:** Always use `lib.makeBinPath` in systemd services.

### Python (Agent Logic & Tooling)
- **Formatting & Linting:** All Python code is formatted and linted with `ruff`.
- **Style:** 
  - Prefer clear, descriptive variable names.
  - Use `argparse` for all CLI tools.
  - Maintain a consistent logging format: `[$(date)] JBot (AgentName): Message`.

---

## 3. Coordination & Task Management

### TASKS.md (The Blackboard)
All work MUST be tracked in `TASKS.md` using the following lifecycle:
- **Backlog:** Unassigned ideas.
- **Proposal:** Complex changes requiring research/design first.
- **To Do / In Progress:** Active work assigned to an `(Agent: Name)`.
- **In Review (Human):** HIL gatekeeping state. No file-mutating tools allowed.
- **Done:** Verified and completed work.

### Agent Communication
- **Shared History:** Use `.jbot/memory.log` for high-level summaries of agent actions.
- **Direct Messaging:** Use `.jbot/messages/` for agent-to-agent coordination.

---

## 4. Development Workflow

### Testing
- **Unit Tests:** Located in `tests/`. Run via `nix flake check --no-build`.
- **Integration Tests:** Use `nixos-test.nix` for full VM-based verification.
- **Reproduction:** Bug fixes must include a reproduction test case.

### Commit Messages
Follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/):
- `feat(nix): ...`
- `fix(agent): ...`
- `docs: ...`
- `chore(scripts): ...`

### Git Hooks
All hooks live in `.githooks/` and are automatically activated by the dev shell:
- **`pre-commit`**: Checks Nix and Python formatting and linting.
- **`commit-msg`**: Validates Conventional Commits format.
- **`pre-push`**: Runs full suite of tests.

### Directory Structure
- `/scripts/`: All Python-based agent logic and utility scripts.
- `/tests/`: Nix-based unit and integration tests.
- `/docs/`: Long-form documentation and architectural archives.
- `/examples/`: Example configurations for users.
