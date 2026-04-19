# JBot

Autonomous AI agent scheduler for NixOS.

## Overview

JBot is a Home Manager module that defines the `programs.jbot` namespace to schedule the Gemini CLI via `systemd.user`. It provides a hard-sandboxed environment for an AI developer agent to operate within your project directory, utilizing a specialized system prompt and RAG-based context injection.

## Getting Started

1.  Include `jbot.nix` in your Home Manager configuration.
2.  Enable JBot and define your agents:
    ```nix
    programs.jbot = {
      enable = true;
      agents.main = {
        enable = true;
        role = "Lead Developer";
        description = "Maintain and improve the JBot codebase.";
        projectDir = "/path/to/your/project";
        interval = "hourly";
      };
      agents.qa = {
        enable = true;
        role = "QA Specialist";
        description = "Review code changes and run tests.";
        projectDir = "/path/to/your/project";
        interval = "daily";
        dependsOn = [ "main" ]; # Run after 'main'
        extraPackages = [ pkgs.gh ]; # Add GitHub CLI for PR reviews
      };
    };
    ```
3.  Enter the development environment:
    ```bash
    nix develop
    ```

## Features

- **Multi-Agent Support**: Define multiple agents with specialized roles and descriptions (e.g., Lead Developer, QA, CEO).
- **Autonomous Scheduling**: Runs Gemini CLI for each agent at regular intervals via systemd user timers.
- **Strict Sandboxing**: Isolated execution environment with `bubblewrap` and systemd sandboxing (read-only home, restricted paths).
- **Context Injection**: Automatically injects project goals, directory structure, Task Board (`TASKS.md`), and agent-specific role/description into the prompt.
- **Shared Memory**: Agents working on the same project directory can collaborate through a shared memory log.
- **Task Board (Blackboard)**: Dedicated `TASKS.md` manager for agents to claim, update, and track work status across different roles.
