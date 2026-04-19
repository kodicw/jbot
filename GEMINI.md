# GEMINI.md - JBot Project Context

This document provides foundational instructions and context for the JBot project.

## Project Overview
JBot is a Nix-based infrastructure project that enables autonomous AI developer agents on NixOS via Home Manager. It schedules the Gemini CLI to run at periodic intervals within a strictly sandboxed `systemd.user` service.

### Main Technologies
- **Nix (Flakes & Home Manager)**: Used for environment reproducibility and system configuration.
- **Gemini CLI**: The core AI agent engine.
- **Systemd**: Manages the agent's execution lifecycle via user services and timers.
- **Python 3**: Utilized as a robust helper for multiline context injection into agent prompts.
- **Bash**: Orchestrates the execution loop and handles sandboxing configurations.

### Architecture
1.  **`jbot.nix`**: The core Home Manager module. It defines the `programs.jbot` options and the `systemd.user.services.jbot-agent`.
2.  **`jbot_prompt.txt`**: The "brain" of the agent, containing operational directives, research strategies, and output format requirements.
3.  **Context Injection**: The `jbot-loop` script dynamically populates `{PROJECT_GOAL}`, `{DIRECTORY_TREE}`, and `{RAG_DATABASE_RESULTS}` placeholders using Python before passing the final prompt to the agent.
4.  **Sandboxing**: Execution is restricted using `ProtectSystem=strict`, `ProtectHome=read-only`, and `BindPaths` to ensure the agent only modifies the designated project directory.

## Building and Running

### Development Environment
To enter the project development shell:
```bash
nix develop
```

### Formatting & Linting
- **Nix Formatting**: `nix run nixpkgs#nixfmt -- <file.nix>`
- **Nix Linting**: `nix run nixpkgs#statix -- check <file.nix>`

### Testing & Validation
Since JBot is a Home Manager module, validation typically involves:
1.  Checking Nix syntax: `nix-instantiate --parse <file.nix>`
2.  Applying the module in a local Home Manager configuration.
3.  Verifying the generated systemd unit: `systemctl --user cat jbot-agent.service`

## Development Conventions

### Coding Style
- **Nix**: Follow the RFC-style formatting. Use `lib.makeBinPath` for service environments to ensure hermeticity.
- **Shell**: Use `set -euo pipefail` in all scripts.
- **Prompts**: Maintain placeholders in `jbot_prompt.txt` and ensure the agent's output is restricted to executable shell commands as per its directives.

### Commit Messages
Follow **Conventional Commits**. Common scopes include:
- `nix`: Changes to `jbot.nix` or `flake.nix`.
- `prompt`: Updates to `jbot_prompt.txt`.
- `docs`: Documentation updates.
- `hm`: Home Manager specific logic.

### Engineering Standards
- **Surgical Updates**: Use targeted `replace` calls for Nix expressions.
- **Reproducibility**: Always prefer passing packages via `pkgs` in Nix expressions rather than relying on the global PATH.
- **Security**: Never loosen sandboxing without a documented security rationale.
