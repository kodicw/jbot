# Formal Directives System

Directives are high-priority, non-negotiable architectural or strategic rules that are injected into every agent's prompt with maximum precedence.

## How it Works
1.  **Storage:** Directives are stored as individual `.txt` or `.md` files in `.jbot/directives/`.
2.  **Injection:** The `jbot-agent.py` script will read all files in this directory and inject them into a `{FORMAL_DIRECTIVES}` placeholder in the prompt template.
3.  **Authority:** Only "Supervisor" agents (e.g., CEO, Principal Architect) should create or modify directives.

## Active Directives
(None yet)

## Guidelines
- Directives should be concise.
- Directives should focus on "How" we build (e.g., "Always use Vanilla CSS", "Prefer Nix expressions over shell scripts").
- Use directives sparingly to avoid prompt bloat.
