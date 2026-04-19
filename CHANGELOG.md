# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Home Manager module `jbot.nix` for scheduling the AI agent.
- `jbot_prompt.txt` with robust context injection.
- Strict sandboxing for the `jbot-agent` systemd service.
- Python-based multiline placeholder replacement in the execution script.
- **Added `jq` to the JBot environment for better JSON processing.**
- **Implemented `.memory_queue.json` to `.memory.log` persistence loop.**
- **Added `.project_goal` file for dynamic project objective management.**
- **Improved Python context injection using environment variables for robustness.**

### Changed
- Refactored project documentation to match JBot's identity.

## [1.0.0] - 2026-04-19

### Added
- Initial creation of JBot infrastructure.
- Standard engineering documents (CONTRIBUTING, GOVERNANCE, etc.).
- Nix development environment.
