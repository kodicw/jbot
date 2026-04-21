import os
import sys
import subprocess
import json
from datetime import datetime
import jbot_utils as utils

def main():
    project_dir = os.environ.get("PROJECT_DIR", os.getcwd())
    os.chdir(project_dir)

    utils.log("Starting infrastructure maintenance...", "Maintenance")

    # 0. Infrastructure Initialization
    for d in [
        ".jbot/queues",
        ".jbot/messages",
        ".jbot/directives",
        ".jbot/messages/archive",
        ".jbot/directives/archive",
    ]:
        if not os.path.exists(d):
            os.makedirs(d, exist_ok=True)
            utils.log(f"Initialized directory: {d}", "Maintenance")

    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 1. Memory Consolidation
    queues_dir = ".jbot/queues"
    memory_log = ".jbot/memory.log"
    if os.path.exists(queues_dir):
        for q_file in os.listdir(queues_dir):
            if q_file.endswith(".json"):
                q_path = os.path.join(queues_dir, q_file)
                agent_name = q_file[:-5]
                utils.log(f"Consolidating memory from {agent_name}...", "Maintenance")
                try:
                    content = utils.load_json(q_path)
                    with open(memory_log, "a") as f:
                        f.write(
                            json.dumps(
                                {
                                    "agent": agent_name,
                                    "content": content,
                                    "timestamp": datetime.now().isoformat(),
                                }
                            )
                            + "\n"
                        )
                    os.remove(q_path)
                except Exception as e:
                    utils.log(f"Error consolidating {q_path}: {e}", "Maintenance")

    # 2. Automated Purging & Rotation
    for script in [
        "jbot-purge.py",
        "jbot-rotate.py",
        "jbot-rotate-tasks.py",
        "jbot-rotate-messages.py",
        "jbot-dashboard.py",
    ]:
        script_path = os.path.join(script_dir, script)
        if os.path.exists(script_path):
            try:
                utils.log(f"Running {script}...", "Maintenance")
                subprocess.run(["python3", script_path], check=True)
            except Exception as e:
                utils.log(f"Error running {script}: {e}", "Maintenance")

    utils.log("Maintenance complete.", "Maintenance")

if __name__ == "__main__":
    main()
