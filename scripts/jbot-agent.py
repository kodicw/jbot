import os
import sys
import json
import subprocess
import tempfile
import re
from datetime import datetime
import jbot_utils as utils

def main():
    agent_name = os.environ.get("AGENT_NAME")
    agent_role = os.environ.get("AGENT_ROLE")
    agent_desc = os.environ.get("AGENT_DESCRIPTION")
    project_dir = os.environ.get("PROJECT_DIR")
    prompt_file = os.environ.get("PROMPT_FILE")
    gemini_pkg = os.environ.get("GEMINI_PACKAGE", "gemini")

    if not all([agent_name, agent_role, project_dir, prompt_file]):
        print("Error: Missing required environment variables.")
        sys.exit(1)

    os.chdir(project_dir)

    # Setup directories
    for d in [".jbot/queues", ".jbot/memory", ".jbot/messages", ".jbot/directives", ".jbot/lock"]:
        os.makedirs(d, exist_ok=True)

    utils.log(f"Starting execution loop as {agent_role}...", agent_name)

    # Find core files upwards
    tasks_path = utils.find_file_upwards("TASKS.md", project_dir) or "TASKS.md"
    goal_path = utils.find_file_upwards(".project_goal", project_dir) or ".project_goal"

    # Consolidation & Rotation Locking
    rotation_lock = ".jbot/rotation.lock"

    # 1. Automated Purging & Rotation (with locking)
    try:
        os.mkdir(rotation_lock)
        script_dir = os.path.dirname(os.path.abspath(__file__))

        for script in ["jbot-purge.py", "jbot-rotate.py", "jbot-rotate-tasks.py", "jbot-rotate-messages.py"]:
            script_path = os.path.join(script_dir, script)
            if os.path.exists(script_path):
                try:
                    utils.log(f"Running {script}...", agent_name)
                    subprocess.run(["python3", script_path], check=True)
                except Exception as e:
                    utils.log(f"Error running {script}: {e}", agent_name)

        os.rmdir(rotation_lock)
    except FileExistsError:
        utils.log("Rotation lock active. Skipping rotation for this run.", agent_name)

    # 2. Consolidation
    lock_dir = ".jbot/lock/consolidation"
    try:
        os.mkdir(lock_dir)
        queues_dir = ".jbot/queues"
        memory_log = ".jbot/memory.log"
        for q_file in os.listdir(queues_dir):
            if q_file.endswith(".json"):
                q_path = os.path.join(queues_dir, q_file)
                other_agent = q_file[:-5]
                utils.log(f"Consolidating memory from {other_agent}...", agent_name)
                try:
                    content = utils.load_json(q_path)
                    with open(memory_log, "a") as f:
                        f.write(json.dumps({
                            "agent": other_agent,
                            "content": content,
                            "timestamp": datetime.now().isoformat()
                        }) + "\n")
                    os.remove(q_path)
                except Exception as e:
                    utils.log(f"Error consolidating {q_path}: {e}", agent_name)
        os.rmdir(lock_dir)
    except FileExistsError:
        pass  # Another agent is consolidating

    # Prepare Context
    if os.path.exists(".git"):
        try:
            tree = subprocess.check_output(["git", "ls-files"], text=True).strip()
            lines = tree.split("\n")
            if len(lines) > 50:
                tree = "\n".join(lines[:50]) + "\n... (truncated)"
        except Exception:
            tree = "Error running git ls-files"
    else:
        tree_cmd = ["find", ".", "-maxdepth", "2", "-not", "-path", "*/.*", "-not", "-path", "*/__pycache__*", "-not", "-path", "*/tests*"]
        tree = subprocess.check_output(tree_cmd, text=True).strip()

    goal = utils.read_file(goal_path, "Maintain and improve the JBot project infrastructure.")

    # Memory / RAG
    logs = utils.get_recent_logs(".jbot/memory.log", 10)
    rag_entries = []
    seen_summaries = set()
    for entry in logs:
        agent = entry.get("agent")
        summary = entry.get("content", {}).get("summary", "").strip()
        if summary and summary not in seen_summaries:
            rag_entries.append(f"[{agent}] {summary}")
            seen_summaries.add(summary)
    rag_entries.reverse()
    rag_formatted = "\n".join(rag_entries) if rag_entries else "No previous memory found."

    task_board = utils.read_file(tasks_path, f"No Task Board found at {tasks_path}. Please initialize it if needed.")

    # Team Registry
    agents = utils.get_team_registry(project_dir)
    registry_lines = [f"- {name}: {info.get('role')} ({info.get('description')})" for name, info in agents.items() if name != agent_name]
    team_registry = "\n".join(registry_lines) if registry_lines else "No other agents in visibility."

    # Messages
    msgs_dir = ".jbot/messages"
    human_input = "No direct human feedback for this cycle."
    human_file = os.path.join(msgs_dir, "human.txt")
    if os.path.exists(human_file):
        human_input = f"--- HUMAN FEEDBACK/DIRECTIVE ---\n{utils.read_file(human_file)}\n--- END HUMAN FEEDBACK ---"
        utils.log("Injected human feedback from human.txt", agent_name)

    recent_msgs = utils.get_recent_messages(msgs_dir, 5)
    messages = "\n".join([f"--- Message {m['filename']} ---\n{m['content']}" for m in recent_msgs]) if recent_msgs else "No recent messages."

    # Directives
    dir_list = utils.parse_directives(".jbot/directives")
    directives = "\n".join([f"--- Directive {d['filename']} ---\n{d['content']}" for d in dir_list]) if dir_list else "No formal directives."

    # Read and replace prompt
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

    with tempfile.NamedTemporaryFile(mode="w", delete=False) as tf:
        tf.write(prompt_content)
        prepared_prompt_path = tf.name

    # Set up memory output for gemini
    os.environ["MEMORY_OUTPUT"] = f".jbot/queues/{agent_name}.json"

    utils.log("Invoking Gemini CLI...", agent_name)

    # Capture output for token tracking
    full_output = []
    try:
        process = subprocess.Popen([gemini_pkg, "-y", "-d", "-p", prompt_content], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            print(line, end="", flush=True)
            full_output.append(line)
        process.wait()
        
        if process.returncode != 0:
            utils.log(f"Error: Gemini CLI failed with exit code {process.returncode}", agent_name)
            sys.exit(process.returncode)

        # Update Billing
        utils.update_billing_data(project_dir, 0.01)
        utils.log("Updated billing.", agent_name)

        # Update Dashboard
        dashboard_script = os.path.join(script_dir, "jbot-dashboard.py")
        if os.path.exists(dashboard_script):
            try:
                utils.log("Updating INDEX.md dashboard...", agent_name)
                subprocess.run(["python3", dashboard_script], check=True)
            except Exception as e:
                utils.log(f"Error updating dashboard: {e}", agent_name)

        # Final Verification
        pre_commit_script = os.path.join(project_dir, ".githooks/pre-commit")
        if os.path.exists(pre_commit_script):
            try:
                utils.log("Running final pre-commit verification...", agent_name)
                subprocess.run(["bash", pre_commit_script], check=True)
            except Exception as e:
                utils.log(f"WARNING: Pre-commit verification failed: {e}", agent_name)

    except Exception as e:
        utils.log(f"Error: Execution failed: {e}", agent_name)
        sys.exit(1)
    finally:
        if os.path.exists(prepared_prompt_path):
            os.remove(prepared_prompt_path)

    utils.log("Execution loop finished.", agent_name)

if __name__ == "__main__":
    main()
