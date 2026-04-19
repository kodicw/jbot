# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Professional Autonomous Organization (PAO)** governance model.
- **Formal Directives** system with expiration logic.
- **Billing & Token Tracking** infrastructure.
- **Human-in-the-Loop (HIL)** task states in `TASKS.md`.
- **Dynamic Goal Steering** based on `.project_goal`.
- Updated `README.md` with PAO Team Registry.
- Added `GOVERNANCE.md` to define PAO roles and responsibilities.

### Changed
- Refactored `jbot-agent.py` to support directive injection and token parsing.
- Enhanced `jbot.nix` with project-specific `agents.json` filtering.
- Improved multi-agent handover verification in NixOS tests.

## [1.0.0] - 2026-04-19

### Added
- Initial creation of JBot infrastructure.
- Standard engineering documents (CONTRIBUTING, GOVERNANCE, etc.).
- Nix development environment.
