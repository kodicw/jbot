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

    # Final Prompt Assembly
    replacements = {
        "{AGENT_NAME}": agent_name,
        "{AGENT_ROLE}": agent_role,
        "{AGENT_DESCRIPTION}": agent_desc,
        "{PROJECT_GOAL}": goal,
        "{DIRECTORY_TREE}": tree,
        "{ADDITIONAL_CONTEXT}": realtime_context,
        "{ENVIRONMENT_AUDIT}": env_audit,
        "{RAG_DATABASE_RESULTS}": rag_formatted,
        "{TASK_BOARD}": task_board,
        "{TEAM_REGISTRY}": team_registry,
        "{MESSAGES}": messages,
        "{DIRECTIVES}": directives,
        "{HUMAN_INPUT}": f"{human_input}\n\n--- IDEAS ---\n{fresh_ideas}",
    }

    for k, v in replacements.items():
        prompt_content = prompt_content.replace(k, str(v))

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

    core.log(f"Starting SAEM execution loop as {role}...", name)

    # 1. Create Workspace (COW copy of project in tmpfs)
    workspace_base = os.path.join(tempfile.gettempdir(), f"jbot-workspace-{name}")
    if os.path.exists(workspace_base):
        shutil.rmtree(workspace_base)
    os.makedirs(workspace_base)

    core.log(f"Creating isolated workspace at {workspace_base}...", name)
    try:
        # Prefer COW reflink, fallback to hardlinks
        try:
            subprocess.run(
                ["cp", "-a", "--reflink=always", f"{project_dir}/.", workspace_base],
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError:
            core.log("COW reflink failed, falling back to hardlinks...", name)
            subprocess.run(
                ["cp", "-al", f"{project_dir}/.", workspace_base], check=True
            )
    except Exception as e:
        core.log(f"Error creating workspace: {e}", name)
        sys.exit(1)

    os.chdir(workspace_base)

    # 2. Prepare workspace infrastructure
    queues_dir = ".jbot/queues"
    outbox_dir = ".jbot/outbox"
    os.makedirs(queues_dir, exist_ok=True)
    os.makedirs(outbox_dir, exist_ok=True)

    # 3. Assemble context
    prompt_content = assemble_context(
        name, role, description, workspace_base, prompt_file
    )

    # Set up memory output for gemini
    os.environ["MEMORY_OUTPUT"] = f"{workspace_base}/{queues_dir}/{name}.json"

    core.log("Invoking Gemini CLI in workspace...", name)

    # 4. Execution
    try:
        process = subprocess.Popen(
            [gemini_pkg, "-y", "-d", "-p", prompt_content],
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

        # 5. Verification
        pre_commit_script = os.path.join(workspace_base, ".githooks/pre-commit")
        verified = False
        if os.path.exists(pre_commit_script):
            try:
                core.log("Running workspace verification (pre-commit)...", name)
                subprocess.run(["bash", pre_commit_script], check=True)
                verified = True
                core.log("Verification SUCCESS.", name)
            except subprocess.CalledProcessError as e:
                core.log(f"Verification FAILED: {e}", name)
        else:
            core.log("No verification script found, skipping...", name)
            verified = True

        # 6. Atomic Application
        if verified:
            core.log("Applying changes back to project directory...", name)
            try:
                subprocess.run(
                    [
                        "rsync",
                        "-a",
                        "--exclude",
                        ".jbot/queues",
                        "--exclude",
                        ".jbot/outbox",
                        f"{workspace_base}/",
                        f"{project_dir}/",
                    ],
                    check=True,
                )
                # Move state files to the REAL project dir for maintenance
                for d in [queues_dir, outbox_dir]:
                    src_d = os.path.join(workspace_base, d)
                    dst_d = os.path.join(project_dir, d)
                    os.makedirs(dst_d, exist_ok=True)
                    for f in os.listdir(src_d):
                        shutil.move(os.path.join(src_d, f), os.path.join(dst_d, f))
                core.log("Transactional commit SUCCESS.", name)
            except Exception as e:
                core.log(f"Error applying changes: {e}", name)
                sys.exit(1)
        else:
            core.log("Changes discarded due to verification failure.", name)

    except Exception as e:
        core.log(f"Error: Execution failed: {e}", name)
        sys.exit(1)
    finally:
        core.log("Cleaning up workspace...", name)
        shutil.rmtree(workspace_base, ignore_errors=True)

    core.log("SAEM execution loop finished.", name)


def main():
    """CLI entry point for run_agent."""
    run_agent()


if __name__ == "__main__":
    main()
