# Contributing Guide: Code Standards & Engineering Practices

**Project:** JBot  
**Version:** 1.0.1  
**Date:** 2026-04-19

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

All commits follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification. This is enforced by the `commit-msg` hook defined in [§5](#5-git-hooks).

### Format

```
<type>(<scope>): <subject>

[optional body]

[optional footer(s)]
```

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

### Scope

Scope is the module or layer being changed. Common scopes:

| Scope | Maps to |
|---|---|
| `nix` | `jbot.nix`, `flake.nix` — all Nix expressions |
| `prompt` | `jbot_prompt.txt` — system prompt configuration |
| `docs` | Documentation updates (README, CONTRIBUTING, etc.) |
| `hm` | Home Manager module logic and integration |

Scope is optional but strongly encouraged. Omit it only for cross-cutting changes.

### Subject Rules

- Imperative mood, present tense: "add handler" not "added handler"
- No capital first letter
- No trailing period
- Maximum 72 characters for the full first line

### Examples

```
feat(cli): add python template support
fix(template): fix rust template clippy lints
refactor(nix): simplify flake outputs structure
test(template): add integration test for project creation
chore(nix): bump nixpkgs input to 24.11
docs: add template usage examples
```

### Body and Footers

Use the body to explain **why**, not what. The diff explains what.

```
fix(cli): handle missing template directory gracefully

Previously, the CLI would panic if the templates directory
was not found. Now it displays a helpful error message.

Closes #42
```

Footer tokens:

| Token | Purpose |
|---|---|
| `Closes #N` | Links and closes a GitHub issue |
| `Refs #N` | References an issue without closing it |
| `BREAKING CHANGE:` | Documents a breaking API or schema change |

---

## 2. Branch Strategy

This project uses a **trunk-based development** model with short-lived feature branches. `main` is always in a releasable state.

### Branch Naming

```
<type>/<short-description>
```

Use the same type vocabulary as commit messages. Description is kebab-case, no more than 5 words.

```
feat/add-python-template
fix/cli-template-resolution
refactor/flake-outputs-structure
chore/bump-nixpkgs-2411
docs/template-usage-guide
```

### Branch Lifecycle

```
main
 │
 ├── feat/add-python-template      ← short-lived, < 2 days preferred
 │    ├── (commits)
 │    └── PR → squash merge → main
 │
 ├── fix/cli-template-resolution
 │    ├── (commits)
 │    └── PR → squash merge → main
 │
 └── ...
```

### Rules

- **Never commit directly to `main`.** All changes go through a PR.
- **One concern per branch.** A branch that fixes a bug and adds a feature will be asked to split.
- **Branches must be rebased on `main` before merge**, not merged into. This keeps a linear history.
- **Delete branches after merge.** Stale branches are noise.
- **Branch lifetimes over 3 days require a comment** in the PR explaining why.

### Protected Branch: `main`

- Requires at least one passing `nix flake check` run (CI)
- Requires PR review before merge
- No force-push
- Linear history enforced (rebase merges only, no merge commits)

---

## 3. Test-Driven Development

This project practices strict TDD. No production code is written without a failing test first. The cycle is **Red → Green → Refactor**, without exception.

### The Cycle

```
┌─────────────────────────────────────────────────┐
│                                                 │
│   1. RED    Write a failing test that           │
│             describes the desired behavior.     │
│             Run it. Watch it fail.              │
│                    │                            │
│                    ▼                            │
│   2. GREEN  Write the minimum production        │
│             code to make the test pass.         │
│             No more, no less.                   │
│                    │                            │
│                    ▼                            │
│   3. REFACTOR  Clean up the code. Extract,     │
│             rename, simplify. The test          │
│             suite must stay green.              │
│                    │                            │
│                    └─────────────────────────┐  │
│                                              │  │
│             Repeat for the next behavior.    │  │
│                                              ▼  │
└─────────────────────────────────────────────────┘
```

### Test Layers

#### Unit Tests (Rust — `cargo test`)

Live in `src/` as `#[cfg(test)]` modules at the bottom of each source file. They test a single function or type in isolation, with no I/O.

**When to write:**
- Every pure function in the CLI
- Every error path (invalid input, missing files)
- Template processing logic

**Example:**

```rust
// src/main.rs

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_template_name_validation() {
        let valid = is_valid_template_name("rust");
        assert!(valid);

        let invalid = is_valid_template_name("invalid!");
        assert!(!invalid);
    }

    #[test]
    fn test_project_name_default() {
        let name = default_project_name("rust");
        assert_eq!(name, "rust-project");
    }
}
```

#### Integration Tests (nixosTest — QEMU)

Not typically needed for template projects unless you're testing NixOS module templates with actual VM deployment.

Run with:

```bash
nix flake check
# or targeted:
nix build .#checks.x86_64-linux.integration --print-build-logs
```

### What Requires a Test First

| Code change | Required test layer |
|---|---|
| New CLI flag/option | Unit test |
| New template | Integration test (create and verify template works) |
| New NixOS module option | nixosTest assertion |
| Bug fix | Unit test that reproduces the bug, then fix |

### What Does Not Need a Test First

- Documentation changes
- Nix expression formatting (no behavior)
- Comment rewrites

### Running Tests

```bash
# Unit tests only (fast, no QEMU)
cargo test

# Unit tests with output
cargo test -- --nocapture

# Specific test
cargo test test_template_name_validation

# Full integration suite (slow, spawns QEMU VM)
nix flake check

# Check compilation without running
cargo check
```

---

## 4. Code Style & Formatting

### Rust

All Rust code is formatted with `rustfmt` using the project's `rustfmt.toml`. No manual formatting decisions — the formatter is authoritative.

Run formatter:

```bash
cargo fmt
```

Check without modifying (used in hooks):

```bash
cargo fmt -- --check
```

All Rust code is linted with `clippy`. The project treats warnings as errors:

```bash
cargo clippy -- -D warnings
```

The following clippy lints are explicitly enabled in `Cargo.toml`:

```toml
[lints.clippy]
unwrap_used = "warn"          # prefer expect() with message or proper error handling
panic = "warn"                # no panics in library code paths
todo = "warn"                 # no committed TODOs
dbg_macro = "warn"            # no debug macros in committed code
print_stdout = "warn"         # use tracing, not println!
```

### Nix

All Nix files are formatted with `nixfmt` (the RFC-style formatter). No nixpkgs-fmt.

```bash
nixfmt flake.nix nix/
```

Check without modifying:

```bash
nixfmt --check flake.nix nix/
```

Linting with `statix`:

```bash
statix check .
```

`statix` catches common Nix anti-patterns: unnecessary `with`, deprecated `builtins`, redundant `let ... in`.

### Templates

Template files use `${PROJECT_NAME}` and `${PROJECT_DESCRIPTION}` placeholders that are replaced during project creation. Keep placeholders consistent across all templates.

---

## 5. Git Hooks

All hooks live in `.githooks/` and are activated by the dev shell (see §7). They are checked into the repository — every developer runs the same hooks.

### Hook: `pre-commit`

Runs on every `git commit`. Blocks the commit if any check fails.

**File: `.githooks/pre-commit`**

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "[pre-commit] Running checks..."

# 1. Rust formatting
echo "  -> cargo fmt --check"
cargo fmt -- --check
if [ $? -ne 0 ]; then
  echo ""
  echo "  FAIL: Rust formatting issues found."
  echo "  Run 'cargo fmt' to fix, then re-stage."
  exit 1
fi

# 2. Clippy linting
echo "  -> cargo clippy"
cargo clippy -- -D warnings 2>&1
if [ $? -ne 0 ]; then
  echo ""
  echo "  FAIL: Clippy found warnings (treated as errors)."
  echo "  Fix the issues above, then re-stage."
  exit 1
fi

# 3. Nix formatting
echo "  -> nixfmt --check"
nixfmt --check flake.nix 2>&1
if [ $? -ne 0 ]; then
  echo ""
  echo "  FAIL: Nix formatting issues found."
  echo "  Run 'nixfmt flake.nix' to fix, then re-stage."
  exit 1
fi

# 4. statix lint
echo "  -> statix check"
statix check . 2>&1
if [ $? -ne 0 ]; then
  echo ""
  echo "  FAIL: statix found Nix anti-patterns."
  echo "  Run 'statix fix .' to auto-fix where possible."
  exit 1
fi

# 5. Rust unit tests
echo "  -> cargo test"
cargo test --quiet 2>&1
if [ $? -ne 0 ]; then
  echo ""
  echo "  FAIL: Unit tests failed."
  echo "  Fix failing tests before committing."
  exit 1
fi

echo ""
echo "[pre-commit] All checks passed."
```

### Hook: `commit-msg`

Validates the commit message format against the Conventional Commits specification.

**File: `.githooks/commit-msg`**

```bash
#!/usr/bin/env bash
set -euo pipefail

COMMIT_MSG_FILE="$1"
COMMIT_MSG=$(cat "$COMMIT_MSG_FILE")

# Allow merge commits and fixup commits through unchanged
if echo "$COMMIT_MSG" | grep -qE "^(Merge|Revert|fixup!|squash!)"; then
  exit 0
fi

# Conventional Commits pattern:
# type(scope)!: subject   — breaking change with scope
# type!: subject          — breaking change without scope
# type(scope): subject    — with scope
# type: subject           — without scope
PATTERN="^(feat|fix|refactor|test|chore|docs|perf|ci|revert)(\([a-z0-9/-]+\))?(!)?: .{1,72}$"

FIRST_LINE=$(echo "$COMMIT_MSG" | head -n 1)

if ! echo "$FIRST_LINE" | grep -qE "$PATTERN"; then
  echo ""
  echo "  FAIL: Commit message does not follow Conventional Commits format."
  echo ""
  echo "  Expected:  <type>(<scope>): <subject>"
  echo "  Got:       $FIRST_LINE"
  echo ""
  echo "  Valid types: feat fix refactor test chore docs perf ci revert"
  echo "  Valid scopes: cli template nix docs"
  echo ""
  echo "  Examples:"
  echo "    feat(cli): add python template support"
  echo "    fix(template): fix rust template clippy lints"
  echo "    chore(nix): bump nixpkgs input to 24.11"
  echo ""
  exit 1
fi

# Subject must not start with a capital letter
SUBJECT=$(echo "$FIRST_LINE" | sed 's/^[^:]*: //')
FIRST_CHAR=$(echo "$SUBJECT" | cut -c1)
if echo "$FIRST_CHAR" | grep -qE "[A-Z]"; then
  echo ""
  echo "  FAIL: Commit subject must start with a lowercase letter."
  echo "  Got: '$SUBJECT'"
  echo ""
  exit 1
fi

# Subject must not end with a period
if echo "$FIRST_LINE" | grep -qE "\.$"; then
  echo ""
  echo "  FAIL: Commit subject must not end with a period."
  echo ""
  exit 1
fi

exit 0
```

### Hook: `pre-push`

Runs the full `nix flake check` before any push to remote. This is the heaviest hook — it spins up a QEMU VM for integration tests. It runs on push rather than commit to keep the commit loop fast.

**File: `.githooks/pre-push`**

```bash
#!/usr/bin/env bash
set -euo pipefail

REMOTE="$1"
URL="$2"

# Skip the full check when pushing to a personal fork (optional escape hatch)
# Remove this block if you want to enforce checks on all remotes.
if [[ "$URL" == *"fork"* ]]; then
  echo "[pre-push] Skipping full flake check for fork remote."
  exit 0
fi

echo "[pre-push] Running nix flake check (this builds a QEMU VM)..."
echo "           To skip in an emergency: git push --no-verify"
echo ""

nix flake check --print-build-logs 2>&1
if [ $? -ne 0 ]; then
  echo ""
  echo "  FAIL: nix flake check failed."
  echo "  The integration tests must pass before pushing to remote."
  exit 1
fi

echo ""
echo "[pre-push] nix flake check passed. Pushing."
```

### Hook Summary

| Hook | Trigger | Checks | Speed |
|---|---|---|---|
| `pre-commit` | `git commit` | `cargo fmt`, `cargo clippy`, `nixfmt`, `statix`, `cargo test` | ~10–30s |
| `commit-msg` | `git commit` | Conventional Commits format validation | <1s |
| `pre-push` | `git push` | `nix flake check` (full QEMU integration suite) | ~2–5min |

### Bypassing Hooks

Hooks can be bypassed with `--no-verify`. This exists for emergencies only (e.g., a broken hook script, pushing a WIP branch to a personal remote for backup). Using `--no-verify` on a branch targeting `main` is not permitted.

```bash
# Emergency bypass — do not use on branches targeting main
git commit --no-verify -m "wip: debugging hook issue"
git push --no-verify
```

If you bypass a hook, the CI pipeline will catch the same failures. There is no path to `main` that skips the checks.

---

## 6. Pull Request Process

### Opening a PR

1. Ensure your branch is rebased on the latest `main`:
   ```bash
   git fetch origin
   git rebase origin/main
   ```
2. Ensure all local hooks pass (they will run automatically on commit/push).
3. Open the PR with a title that matches the Conventional Commits format:
   ```
   feat(cli): add python template support
   ```
4. Fill in the PR description:
   - **What:** One sentence describing the change.
   - **Why:** Reference to the feature being added or bug being fixed.
   - **How:** Any non-obvious implementation decisions worth noting.
   - **Tests:** Which test cases cover this change.

### Review Checklist

Before approving, reviewers check:

- [ ] All new behavior is covered by a test written before the implementation
- [ ] No `unwrap()` without an `.expect("reason")` or explicit error handling
- [ ] No `println!` or `dbg!` left in committed code (use `tracing`)
- [ ] Nix expressions are formatted and pass `statix check`
- [ ] Commit messages on the branch follow Conventional Commits
- [ ] PR title follows Conventional Commits format
- [ ] `nix flake check` passes in CI

### Merge Strategy

All PRs are **squash-merged** into `main`. The squash commit message is the PR title (which must be Conventional Commits compliant). Individual commits on the branch do not need to be perfectly clean — they are squashed away — but they must pass the `commit-msg` hook for good hygiene during development.

---

## 7. Hook Installation

Hooks are stored in `.githooks/` and must be activated once per clone:

```bash
git config core.hooksPath .githooks
chmod +x .githooks/pre-commit .githooks/commit-msg .githooks/pre-push
```

### Running Hooks

All hooks that invoke Rust tooling (`pre-commit`) execute inside `nix develop` to ensure dependencies (especially the Nix linker for `cargo clippy`) are available. You must be inside a Nix develop shell for hooks to pass:

```bash
nix develop
git commit ...   # pre-commit runs inside nix develop
git push ...     # pre-push runs nix flake check
```

Outside `nix develop`, `cargo clippy` will fail with linker errors because the Nix sandboxed linker (`ld-wrapper.sh`) is not in PATH.

### Via devenv (Recommended)

The `flake.nix` devShell includes a `shellHook` that configures git automatically:

```nix
# In devShell's shellHook
shellHook = ''
  git config core.hooksPath .githooks
  chmod +x .githooks/pre-commit .githooks/commit-msg .githooks/pre-push
  echo "Git hooks activated from .githooks/"
'';
```

Entering the dev shell with `nix develop` or `devenv shell` is sufficient. No manual steps required.

### Verifying Hook Installation

```bash
git config core.hooksPath
# Expected output: .githooks

ls -la .githooks/
# Expected:
# -rwxr-xr-x  commit-msg
# -rwxr-xr-x  pre-commit
# -rwxr-xr-x  pre-push
```

### Required Tools in PATH

All hooks assume the following tools are available. They are provided by the Nix dev shell and do not need to be installed manually:

| Tool | Hook | Provided by |
|---|---|---|
| `cargo` | `pre-commit` | `rustup` / `fenix` in devShell |
| `cargo fmt` | `pre-commit` | `rustfmt` component |
| `cargo clippy` | `pre-commit` | `clippy` component |
| `nixfmt` | `pre-commit` | `nixpkgs.nixfmt-rfc-style` |
| `statix` | `pre-commit` | `nixpkgs.statix` |
| `nix` | `pre-push` | system Nix installation |

Outside the dev shell, hooks that cannot find their tools will fail with a clear error rather than silently passing.

---

## 8. Community & Security

We maintain high standards for community health and infrastructure security. Please refer to the following documents for more information:

- **[Code of Conduct](./CODE_OF_CONDUCT.md)**: Our expectations for participant behavior.
- **[Security Policy](./SECURITY.md)**: How to report vulnerabilities and our security standards.
- **[Support Guide](./SUPPORT.md)**: How to get help with templates and infrastructure.
- **[Governance](./GOVERNANCE.md)**: How decisions are made regarding project standards.
- **[Changelog](./CHANGELOG.md)**: Tracking notable changes to the repository.