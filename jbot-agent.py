#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import tempfile
from datetime import datetime

def log(msg):
    print(f"[{datetime.now()}] JBot: {msg}")

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
    os.makedirs(".jbot/queues", exist_ok=True)
    os.makedirs(".jbot/memory", exist_ok=True)
    os.makedirs(".jbot/messages", exist_ok=True)

    log(f"({agent_name}): Starting execution loop as {agent_role}...")

    # Consolidation
    lock_dir = ".jbot/lock"
    try:
        os.mkdir(lock_dir)
        queues_dir = ".jbot/queues"
        memory_log = ".jbot/memory.log"
        for q_file in os.listdir(queues_dir):
            if q_file.endswith(".json"):
                q_path = os.path.join(queues_dir, q_file)
                other_agent = q_file[:-5]
                log(f"({agent_name}): Consolidating memory from {other_agent}...")
                try:
                    with open(q_path, "r") as f:
                        content = json.load(f)
                    with open(memory_log, "a") as f:
                        f.write(json.dumps({"agent": other_agent, "content": content}) + "\n")
                    os.remove(q_path)
                except Exception as e:
                    log(f"Error consolidating {q_path}: {e}")
        os.rmdir(lock_dir)
    except FileExistsError:
        pass # Another agent is consolidating

    # Prepare Context
    tree = subprocess.check_output(["find", ".", "-maxdepth", "2", "-not", "-path", "*/.*"], text=True).strip()
    
    goal = "Maintain and improve the JBot project infrastructure."
    if os.path.exists(".project_goal"):
        with open(".project_goal", "r") as f:
            goal = f.read().strip()

    rag_formatted = "No previous memory found."
    if os.path.exists(".jbot/memory.log"):
        with open(".jbot/memory.log", "r") as f:
            lines = f.readlines()
            rag_entries = []
            for line in lines[-20:]:
                try:
                    data = json.loads(line)
                    rag_entries.append(f"[{data.get('agent')}] {data.get('content', {}).get('summary')}")
                except:
                    rag_entries.append(line.strip())
            rag_formatted = "\n".join(rag_entries[-10:])

    task_board = "No Task Board found. Please initialize TASKS.md if needed."
    if os.path.exists("TASKS.md"):
        with open("TASKS.md", "r") as f:
            task_board = f.read()

    # Team Registry
    team_registry = "No team registry found."
    if os.path.exists(".jbot/agents.json"):
        with open(".jbot/agents.json", "r") as f:
            agents = json.load(f)
            registry_lines = []
            for name, info in agents.items():
                role_info = f"- {name}: {info.get('role')} ({info.get('description')})"
                if info.get("supervisor"):
                    role_info += f" [Supervisor: {info.get('supervisor')}]"
                registry_lines.append(role_info)
            team_registry = "\n".join(registry_lines)

    # Messages
    messages = "No recent messages."
    msgs_dir = ".jbot/messages"
    if os.path.exists(msgs_dir):
        msg_files = sorted(os.listdir(msgs_dir))
        if msg_files:
            msg_list = []
            for mf in msg_files[-5:]: # Last 5 messages
                with open(os.path.join(msgs_dir, mf), "r") as f:
                    msg_list.append(f"--- Message {mf} ---\n{f.read()}")
            messages = "\n".join(msg_list)

    # Read and replace prompt
    with open(prompt_file, "r") as f:
        prompt_content = f.read()

    replacements = {
        "{AGENT_NAME}": agent_name,
        "{AGENT_ROLE}": agent_role,
        "{AGENT_DESCRIPTION}": agent_desc,
        "{PROJECT_GOAL}": goal,
        "{DIRECTORY_TREE}": tree,
        "{RAG_DATABASE_RESULTS}": rag_formatted,
        "{TASK_BOARD}": task_board,
        "{TEAM_REGISTRY}": team_registry,
        "{MESSAGES}": messages
    }

    for k, v in replacements.items():
        prompt_content = prompt_content.replace(k, str(v))

    with tempfile.NamedTemporaryFile(mode="w", delete=False) as tf:
        tf.write(prompt_content)
        prepared_prompt_path = tf.name

    # Set up memory output for gemini
    os.environ["MEMORY_OUTPUT"] = f".jbot/queues/{agent_name}.json"

    log(f"({agent_name}): Invoking Gemini CLI...")
    
    # We use the environment PATH which should already be set up by bubblewrap/systemd
    try:
        subprocess.run([gemini_pkg, "-y", "-d", "-p", prompt_content], check=True)
    except subprocess.CalledProcessError as e:
        log(f"Error: Gemini CLI failed with exit code {e.returncode}")
        sys.exit(e.returncode)
    finally:
        if os.path.exists(prepared_prompt_path):
            os.remove(prepared_prompt_path)

    log(f"({agent_name}): Execution loop finished.")

if __name__ == "__main__":
    main()
