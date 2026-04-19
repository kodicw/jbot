## What

<!-- Provide a concise, one-sentence description of the change. -->

## Why

<!-- Why is this change necessary? Reference any related issues (e.g., Closes #123). -->

## How

<!-- Describe the technical implementation. How does this impact the NixOS configuration, Dockerfiles, or other infrastructure? -->

## Impact

- **NixOS/Home Manager**: Does this change any system services, sandboxing, or user configurations?
- **Agent Behavior**: Does this modify the prompt or context injection logic?
- **Breaking Change**: Is this a breaking change for existing `programs.jbot` configurations?

## Checklist

- [ ] All new behavior is covered by verification steps.
- [ ] `nix run nixpkgs#statix -- check jbot.nix` passes locally.
- [ ] `nix run nixpkgs#nixfmt -- --check jbot.nix` passes locally.
- [ ] No hardcoded secrets in prompt configuration.
- [ ] Documentation has been updated to reflect the changes.
- [ ] Pull request title follows [Conventional Commits](https://www.conventionalcommits.org/).

## Tests

<!-- Describe the tests you ran to verify your changes. -->
```bash
nix flake check
# or
nix build .#checks.x86_64-linux.integration
```
