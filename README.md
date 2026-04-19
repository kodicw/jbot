# JBot

Autonomous AI agent scheduler for NixOS.

## Overview

JBot is a Home Manager module that defines the `programs.jbot` namespace to schedule the Gemini CLI via `systemd.user`. It provides a hard-sandboxed environment for an AI developer agent to operate within your project directory, utilizing a specialized system prompt and RAG-based context injection.

## Getting Started

1.  Include `jbot.nix` in your Home Manager configuration.
2.  Enable the agent and set your project directory:
    ```nix
    programs.jbot = {
      enable = true;
      projectDir = "/path/to/your/project";
      interval = "hourly";
    };
    ```
3.  Enter the development environment:
    ```bash
    nix develop
    ```

## Features

- **Autonomous Scheduling**: Runs Gemini CLI at regular intervals via systemd user timers.
- **Strict Sandboxing**: Isolated execution environment with read-only home access and restricted networking.
- **Context Injection**: Automatically injects project goals, directory structure, and memory into the agent's prompt.
- **Nix Flake**: Reproducible development environment with `nixfmt` and `statix`.
