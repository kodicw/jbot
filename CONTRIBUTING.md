# Contributing Guide: Code Standards & Engineering Practices

**Project:** JBot  
**Version:** 1.0.1  
**Date:** 2026-04-20

---

## Table of Contents

1. [Commit Messages](#1-commit-messages)
2. [Branch Strategy](#2-branch-strategy)
3. [Test-Driven Development](#3-test-driven-development)
4. [Code Style & Formatting](#4-code-style--formatting)
5. [Git Hooks](#5-git-hooks)
6. [Pull Request Process](#6-pull-request-process)
7. [Hook Installation](#7-hook-installation)
8. [Community & Security](#8-community-and-security)

---

## 1. Commit Messages

All commits follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification.

### Types

| Type | When to use |
|---|---|
| `feat` | A new feature visible to users or operators |
| `fix` | A bug fix |
| `refactor` | Code restructuring with no behavior change |
| `test` | Adding or correcting tests only |
| `chore` | Nix flake updates, dependency bumps, tooling |
| `docs` | Documentation changes only |
| `perf` | Performance improvement |
| `ci` | Changes to CI/CD pipeline or git hooks |
| `revert` | Reverts a previous commit |

---

## 2. Branch Strategy

This project uses a **trunk-based development** model with short-lived feature branches. `main` is always in a releasable state.

---

## 3. Test-Driven Development

### Test Layers

#### Unit Tests

Tests are managed as Nix derivations in `tests/`. They use `runCommand` to verify agent behavior in a controlled environment.

Run with:

```bash
nix flake check --no-build
```

---

## 4. Code Style & Formatting

### Python

All Python code is formatted and linted with `ruff`.

Run formatter:

```bash
ruff format .
```

### Nix

All Nix files are formatted with `nixfmt` (the RFC-style formatter).

```bash
nixfmt .
```

Linting with `statix`:

```bash
statix check .
```

---

## 5. Git Hooks

All hooks live in `.githooks/` and are activated by the dev shell.

### Hook: `pre-commit`
Checks Nix and Python formatting and linting.

### Hook: `commit-msg`
Validates Conventional Commits format.

### Hook: `pre-push`
Runs `nix flake check --no-build`.

---

## 7. Hook Installation

Hooks are automatically activated when entering the dev shell:

```bash
nix develop
```

---

## 8. Community & Security

Refer to the following documents for more information:
- **[Code of Conduct](./CODE_OF_CONDUCT.md)**
- **[Security Policy](./SECURITY.md)**
- **[Support Guide](./SUPPORT.md)**
- **[Governance](./GOVERNANCE.md)**
- **[Changelog](./CHANGELOG.md)**
