import os
import sys
import subprocess
import jbot_utils as utils


def assemble_context(agent_name, agent_role, agent_desc, project_dir, prompt_file):
    """
    Assembles the full context for the agent by reading various infrastructure files.
    """
    # Find key project files
    tasks_path = utils.find_file_upwards("TASKS.md", project_dir) or "TASKS.md"
    goal_path = utils.find_file_upwards(".project_goal", project_dir) or ".project_goal"

    # Directory Tree (Git-aware)
    if os.path.exists(os.path.join(project_dir, ".git")):
        try:
            tree = subprocess.check_output(
                ["git", "-C", project_dir, "ls-files"], text=True
            ).strip()
            lines = tree.split("\n")
            if len(lines) > 50:
                tree = "\n".join(lines[:50]) + "\n... (truncated)"
        except Exception:
            tree = "Error running git ls-files"
    else:
        tree_cmd = [
            "find",
            project_dir,
            "-maxdepth",
            "2",
            "-not",
            "-path",
            "*/.*",
            "-not",
            "-path",
            "*/__pycache__*",
            "-not",
            "-path",
            "*/tests*",
        ]
        try:
            tree = subprocess.check_output(tree_cmd, text=True).strip()
        except Exception:
            tree = "Error generating directory tree"

    goal = utils.read_file(
        goal_path, "Maintain and improve the JBot project infrastructure."
    )

    # Memory / RAG (Shared History)
    logs = utils.get_recent_logs(os.path.join(project_dir, ".jbot/memory.log"), 10)
    rag_entries = []
    seen_summaries = set()
    for entry in logs:
        agent = entry.get("agent")
        summary = entry.get("content", {}).get("summary", "").strip()
        if summary and summary not in seen_summaries:
            rag_entries.append(f"[{agent}] {summary}")
            seen_summaries.add(summary)
    rag_entries.reverse()
    rag_formatted = (
        "\n".join(rag_entries) if rag_entries else "No previous memory found."
    )

    task_board = utils.read_file(
        tasks_path,
        f"No Task Board found at {tasks_path}. Please initialize it if needed.",
    )

    # Team Registry
    agents = utils.get_team_registry(project_dir)
    registry_lines = [
        f"- {name}: {info.get('role')} ({info.get('description')})"
        for name, info in agents.items()
        if name != agent_name
    ]
    team_registry = (
        "\n".join(registry_lines)
        if registry_lines
        else "No other agents in visibility."
    )

    # Messages (Agent-to-Agent)
    msgs_dir = os.path.join(project_dir, ".jbot/messages")
    human_input = "No direct human feedback for this cycle."
    human_file = os.path.join(msgs_dir, "human.txt")
    if os.path.exists(human_file):
        human_input = f"--- HUMAN FEEDBACK/DIRECTIVE ---\n{utils.read_file(human_file)}\n--- END HUMAN FEEDBACK ---"
        utils.log("Injected human feedback from human.txt", agent_name)

    recent_msgs = utils.get_recent_messages(msgs_dir, 5)
    messages = (
        "\n".join(
            [f"--- Message {m['filename']} ---\n{m['content']}" for m in recent_msgs]
        )
        if recent_msgs
        else "No recent messages."
    )

    # Directives (Formal Laws)
    dir_list = utils.parse_directives(os.path.join(project_dir, ".jbot/directives"))
    directives = (
        "\n".join(
            [f"--- Directive {d['filename']} ---\n{d['content']}" for d in dir_list]
        )
        if dir_list
        else "No formal directives."
    )

    # Prompt Preparation
    prompt_content = utils.read_file(prompt_file)
    replacements = {
        "{AGENT_NAME}": agent_name,
        "{AGENT_ROLE}": agent_role,
        "{AGENT_DESCRIPTION}": agent_desc,
        "{PROJECT_GOAL}": goal,
        "{DIRECTORY_TREE}": tree,
        "{RAG_DATABASE_RESULTS}": rag_formatted,
        "{TASK_BOARD}": task_board,
        "{TEAM_REGISTRY}": team_registry,
        "{MESSAGES}": messages,
        "{DIRECTIVES}": directives,
        "{HUMAN_INPUT}": human_input,
    }

    for k, v in replacements.items():
        prompt_content = prompt_content.replace(k, str(v))

    return prompt_content


def run_agent(
    name: str = None,
    role: str = None,
    description: str = None,
    project_dir: str = None,
    prompt_file: str = None,
    gemini_pkg: str = "gemini",
) -> None:
    """Main execution logic for a JBot Agent (Stateless SAEM)."""
    import tempfile
    import shutil

    # Fallback to environment variables if parameters not provided
    name = name or os.environ.get("AGENT_NAME")
    role = role or os.environ.get("AGENT_ROLE")
    description = description or os.environ.get("AGENT_DESCRIPTION")
    project_dir = project_dir or os.environ.get("PROJECT_DIR")
    prompt_file = prompt_file or os.environ.get("PROMPT_FILE")
    gemini_pkg = gemini_pkg or os.environ.get("GEMINI_PACKAGE", "gemini")

    if not all([name, role, project_dir, prompt_file]):
        print(
            f"Error: Missing required parameters or environment variables for agent {name or 'unknown'}."
        )
        sys.exit(1)

    utils.log(f"Starting SAEM execution loop as {role}...", name)

    # 1. Create Workspace (COW copy of project)
    workspace_base = os.path.join(tempfile.gettempdir(), f"jbot-workspace-{name}")
    if os.path.exists(workspace_base):
        shutil.rmtree(workspace_base)
    os.makedirs(workspace_base)

    utils.log(f"Creating isolated workspace at {workspace_base}...", name)
    try:
        # Use --reflink=always for efficient COW copies if possible, fallback to hardlinks
        try:
            subprocess.run(
                ["cp", "-a", "--reflink=always", f"{project_dir}/.", workspace_base],
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError:
            utils.log("COW reflink failed, falling back to hardlinks...", name)
            subprocess.run(
                ["cp", "-al", f"{project_dir}/.", workspace_base],
                check=True,
            )
    except Exception as e:
        utils.log(f"Error creating workspace: {e}", name)
        sys.exit(1)

    os.chdir(workspace_base)

    # 2. Verify write access to outbox and queues in the workspace
    queues_dir = ".jbot/queues"
    outbox_dir = ".jbot/outbox"
    os.makedirs(queues_dir, exist_ok=True)
    os.makedirs(outbox_dir, exist_ok=True)

    # 3. Assemble context (Still reads from workspace, which is a copy of project_dir)
    prompt_content = assemble_context(
        name, role, description, workspace_base, prompt_file
    )

    # Set up memory output for gemini (Redirects agent memory to a queue file in WORKSPACE)
    os.environ["MEMORY_OUTPUT"] = f"{workspace_base}/{queues_dir}/{name}.json"

    utils.log("Invoking Gemini CLI in workspace...", name)

    # 4. Execution (Gemini CLI runs in the workspace)
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
            utils.log(
                f"Error: Gemini CLI failed with exit code {process.returncode}",
                name,
            )
            sys.exit(process.returncode)

        # 5. Verification (Verification of Agent's Output in Workspace)
        pre_commit_script = os.path.join(workspace_base, ".githooks/pre-commit")
        verified = False
        if os.path.exists(pre_commit_script):
            try:
                utils.log("Running workspace verification (pre-commit)...", name)
                subprocess.run(["bash", pre_commit_script], check=True)
                verified = True
                utils.log("Verification SUCCESS.", name)
            except subprocess.CalledProcessError as e:
                utils.log(f"Verification FAILED: {e}", name)
        else:
            utils.log("No verification script found, skipping...", name)
            verified = True  # Treat as success if no verification exists

        # 6. Atomic Application (If verified, sync changes back to project_dir)
        if verified:
            utils.log("Applying changes back to project directory...", name)
            # Use rsync to sync back, excluding .jbot/queues and .jbot/outbox which are handled by maintenance
            # Also exclude .git if we don't want to mess with the host's git state directly
            # Actually, we SHOULD sync .git if the agent made commits in the workspace.
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
                # Also move the queue file and outbox messages manually to the REAL project dir
                # so the maintenance service can find them.
                for d in [queues_dir, outbox_dir]:
                    src_d = os.path.join(workspace_base, d)
                    dst_d = os.path.join(project_dir, d)
                    os.makedirs(dst_d, exist_ok=True)
                    for f in os.listdir(src_d):
                        shutil.move(os.path.join(src_d, f), os.path.join(dst_d, f))

                utils.log("Transactional commit SUCCESS.", name)
            except Exception as e:
                utils.log(f"Error applying changes: {e}", name)
                sys.exit(1)
        else:
            utils.log("Changes discarded due to verification failure.", name)

    except Exception as e:
        utils.log(f"Error: Execution failed: {e}", name)
        sys.exit(1)
    finally:
        # Cleanup workspace
        utils.log("Cleaning up workspace...", name)
        shutil.rmtree(workspace_base, ignore_errors=True)

    utils.log("SAEM execution loop finished.", name)


def main():
    """CLI wrapper for run_agent."""
    run_agent()


if __name__ == "__main__":
    main()
