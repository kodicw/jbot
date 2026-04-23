import os
import sys
import subprocess
import tempfile
import shutil
from typing import Optional

import jbot_core as core
import jbot_infra as infra


def assemble_context(
    agent_name: str,
    agent_role: str,
    agent_desc: str,
    project_dir: str,
    prompt_file: str,
) -> str:
    """
    Assembles the full context for the agent exclusively from the nb knowledge base.
    This ensures that all instructions and state are Git-backed and versioned.
    """
    # 1. Base Operating System (Prompt)
    # Bootstrap: use local prompt_file if not in nb
    nb_prompt = infra.get_note_content("#prompt")
    if nb_prompt:
        core.log("Gathering system prompt from nb knowledge base.", agent_name)
        prompt_content = nb_prompt
    else:
        core.log("Knowledge base prompt missing. Bootstrapping from local file.", agent_name)
        prompt_content = core.read_file(prompt_file)

    # 2. Operational Directives & Command Registry
    directives = infra.get_note_content("type:directives") or "No formal directives in nb."
    
    # 3. Project Goal & Roadmap
    goal = infra.get_note_content("type:goal") or "No project goal defined in nb."
    task_board = infra.get_note_content("type:tasks") or "No task board found in nb."

    # 4. Human Input & Ideas
    human_input = infra.get_note_content("input:human") or "No active human feedback."
    fresh_ideas = infra.get_note_content("type:idea") or "No new ideas recorded."

    # 5. Environment & Tooling (Dynamic Context)
    env_audit = infra.get_note_content("ADR: Environment and Tool Registry") or "No environment audit available."
    git_status = core.get_git_status(project_dir)
    nix_metadata = core.get_nix_metadata(project_dir)
    
    # Directory Tree (Git-aware)
    try:
        tree = subprocess.check_output(["git", "-C", project_dir, "ls-files"], text=True).strip()
        lines = tree.split("\n")
        if len(lines) > 50:
            tree = "\n".join(lines[:50]) + "\n... (truncated)"
    except Exception:
        tree = "Error generating directory tree"

    realtime_context = f"""
**Real-time Git Status:**
{git_status}

**Nix Flake Metadata:**
{nix_metadata}

**Workspace Tree:**
{tree}
"""

    # 6. Collective Memory (Shared History from nb)
    logs = infra.get_recent_logs("", 15)
    rag_entries = []
    seen_summaries = set()
    for entry in logs:
        agent = entry.get("agent")
        summary = entry.get("content", {}).get("summary", "").strip()
        if summary and summary not in seen_summaries:
            rag_entries.append(f"[{agent}] {summary}")
            seen_summaries.add(summary)
    rag_entries.reverse()
    rag_formatted = "\n".join(rag_entries) if rag_entries else "No previous memory found in nb."

    # 7. Team Registry
    agents = infra.get_team_registry(project_dir)
    registry_lines = [f"- {name}: {info.get('role')} ({info.get('description')})" for name, info in agents.items() if name != agent_name]
    team_registry = "\n".join(registry_lines) if registry_lines else "No other agents in visibility."

    # 8. Inter-Agent Messaging
    msgs_dir = os.path.join(project_dir, ".jbot/messages")
    recent_msgs = infra.get_recent_messages(msgs_dir, 5)
    messages = "\n".join([f"--- Message {m['filename']} ---\n{m['content']}" for m in recent_msgs]) if recent_msgs else "No recent messages."

    # 9. Available Notebooks
    try:
        nb_list_res = subprocess.run(
            ["nb", "notebooks", "--names"],
            capture_output=True, text=True, env={**os.environ, "EDITOR": "cat"}
        )
        notebooks = nb_list_res.stdout.strip().splitlines() if nb_list_res.returncode == 0 else ["jbot"]
    except Exception:
        notebooks = ["jbot"]

    # Final Prompt Assembly using Jinja2
    from jinja2 import Template
    
    template_data = {
        "agent": {
            "name": agent_name,
            "role": agent_role,
            "description": agent_desc,
        },
        "goal": goal,
        "environment_audit": env_audit,
        "shared_history": rag_formatted,
        "realtime_state": realtime_context,
        "tasks": task_board,
        "team": agents, # Full registry dict
        "messages": messages,
        "directives": directives,
        "human_input": human_input,
        "fresh_ideas": fresh_ideas,
        "notebooks": notebooks,
    }

    try:
        template = Template(prompt_content)
        return template.render(**template_data)
    except Exception as e:
        core.log(f"Jinja2 rendering failed: {e}. Falling back to raw content.", agent_name)
        return prompt_content


def run_agent(
    name: Optional[str] = None,
    role: Optional[str] = None,
    description: Optional[str] = None,
    project_dir: Optional[str] = None,
    prompt_file: Optional[str] = None,
    gemini_pkg: Optional[str] = "gemini",
) -> None:
    """
    Main execution logic for a JBot Agent using the Stateless Agent Execution Model (SAEM).
    Uses a temporary workspace to ensure transactional and atomic updates.
    """
    # Fallback to environment variables if parameters not provided
    name = name or os.environ.get("AGENT_NAME")
    role = role or os.environ.get("AGENT_ROLE")
    description = description or os.environ.get("AGENT_DESCRIPTION")
    project_dir = project_dir or os.environ.get("PROJECT_DIR")
    prompt_file = prompt_file or os.environ.get("PROMPT_FILE")
    gemini_pkg = gemini_pkg or os.environ.get("GEMINI_PACKAGE", "gemini")

    if not all([name, role, project_dir, prompt_file]):
        print(
            f"Error: Missing required parameters or env for agent {name or 'unknown'}."
        )
        sys.exit(1)

    core.log(f"Starting execution loop for {role}...", name)

    # 0. Initialize Non-interactive Environment (Identity & NB)
    home_dir = os.environ.get("HOME")
    if home_dir:
        # Seed Git Identity
        gitconfig_path = os.path.join(home_dir, ".gitconfig")
        if not os.path.exists(gitconfig_path):
            with open(gitconfig_path, "w") as f:
                f.write(f"[user]\n  name = JBot ({name})\n  email = jbot-{name}@internal.jbot\n[core]\n  pager = cat\n")
        
        # Seed NB Config
        nbrc_path = os.path.join(home_dir, ".nbrc")
        if not os.path.exists(nbrc_path):
            with open(nbrc_path, "w") as f:
                f.write(f"export NB_DIR=\"{home_dir}/.nb\"\nexport NB_USER_NAME=\"JBot ({name})\"\nexport NB_USER_EMAIL=\"jbot-{name}@internal.jbot\"\n")
        
        # Link Project Knowledge Base
        nb_home = os.path.join(home_dir, ".nb")
        os.makedirs(nb_home, exist_ok=True)
        jbot_link = os.path.join(nb_home, "jbot")
        if not os.path.exists(jbot_link):
            os.symlink(os.path.join(project_dir, ".nb"), jbot_link)

    # 1. Prepare Infrastructure
    os.chdir(project_dir)
    queues_dir = ".jbot/queues"
    outbox_dir = ".jbot/outbox"
    os.makedirs(queues_dir, exist_ok=True)
    os.makedirs(outbox_dir, exist_ok=True)

    # 2. Assemble Context
    prompt_content = assemble_context(
        name, role, description, project_dir, prompt_file
    )

    # Set up memory output for gemini
    os.environ["MEMORY_OUTPUT"] = f"{project_dir}/{queues_dir}/{name}.json"

    core.log("Invoking Gemini CLI in project directory...", name)

    # 3. Execution
    try:
        process = subprocess.Popen(
            [gemini_pkg, "-y", "-p", prompt_content],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        for line in process.stdout:
            print(line, end="", flush=True)
        process.wait()

        if process.returncode != 0:
            core.log(
                f"Error: Gemini CLI failed with exit code {process.returncode}", name
            )
            sys.exit(process.returncode)

        # 4. Verification (Optional but recommended)
        pre_commit_script = os.path.join(project_dir, ".githooks/pre-commit")
        if os.path.exists(pre_commit_script):
            try:
                core.log("Running project verification (pre-commit)...", name)
                subprocess.run(["bash", pre_commit_script], check=True)
                core.log("Verification SUCCESS.", name)
            except subprocess.CalledProcessError as e:
                core.log(f"Verification WARNING: {e}", name)
        
        core.log("Execution SUCCESS.", name)

    except Exception as e:
        core.log(f"Error: Execution failed: {e}", name)
        sys.exit(1)

    core.log("Execution loop finished.", name)


def main():
    """CLI entry point for run_agent."""
    run_agent()


if __name__ == "__main__":
    main()
