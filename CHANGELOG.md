# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Infrastructure CLI Integration:** Integrated `maintenance`, `purge`, `rotate`, `dashboard`, and `send-message` as subcommands in the `jbot` CLI.
- **Modularized Infrastructure Logic:** Moved core logic for purging, rotation, and dashboard generation into `scripts/jbot_utils.py` for architectural purity.
- **Consolidated Rotation Logic:** Unified memory, task, and message rotation under a single `jbot rotate` command.
- **Centralized Maintenance:** Implemented `jbot maintenance` to orchestrate all infrastructure tasks.
- **Centralized JBot CLI:** Developed and integrated a unified `jbot` CLI tool for monitoring the organization.

- **Integrated Quality Gates:** Added `nixfmt`, `statix`, and `ruff` checks to `flake.nix` and pre-commit hooks.
- **Git Hooks Configuration:** Fixed and verified automated pre-commit and commit-msg verification.
- **Flat Organization Audit:** Completed full audit and pruning of hierarchical logic from core scripts.
- **Memory Rotation:** Completed and integrated `jbot-rotate.py` for automated context cleanup.
- **Professional Autonomous Organization (organization)** governance model.
- **Formal Directives** system with expiration logic.
- **Human-in-the-Loop (HIL)** task states in `TASKS.md`.
- **INDEX.md dashboard** for organization transparency.
- Integrated `jbot-dashboard.py` into the execution loop.
- **Improved directive expiration parsing** with regex and internal header support.
- **Dynamic Goal Steering** based on `.project_goal`.
- Updated `README.md` with organization Team Registry.
- Added `GOVERNANCE.md` to define organization roles and responsibilities.

### Changed
- Refactored `jbot-agent.py` to support directive injection and token parsing.
- Enhanced `jbot.nix` with project-specific `agents.json` filtering.
- Improved multi-agent handover verification in NixOS tests.

## [1.0.0] - 2026-04-19

### Added
- Initial creation of JBot infrastructure.
- Standard engineering documents (CONTRIBUTING, GOVERNANCE, etc.).
- Nix development environment.
