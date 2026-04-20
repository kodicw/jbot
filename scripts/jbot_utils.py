import os
import json
import re
import subprocess
from datetime import datetime

# --- Logging ---
def log(msg, component="JBot"):
    """Standardized logging format for all JBot scripts."""
    print(f"[{datetime.now()}] {component}: {msg}")

# --- Paths & Files ---
def find_file_upwards(filename, start_dir="."):
    """Search for a file in the current directory and its parents."""
    current = os.path.abspath(start_dir)
    while True:
        target = os.path.join(current, filename)
        if os.path.exists(target):
            return target
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return None

def get_project_root(start_dir="."):
    """Find the project root by looking for .project_goal."""
    goal_path = find_file_upwards(".project_goal", start_dir)
    if goal_path:
        return os.path.dirname(goal_path)
    return os.path.abspath(start_dir)

def load_json(file_path, default=None):
    """Safely load a JSON file."""
    if not os.path.exists(file_path):
        return default if default is not None else {}
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except Exception as e:
        log(f"Error loading JSON from {file_path}: {e}", "Utils")
        return default if default is not None else {}

def save_json(file_path, data):
    """Safely save a JSON file, ensuring the directory exists."""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        log(f"Error saving JSON to {file_path}: {e}", "Utils")

def read_file(file_path, default=""):
    """Safely read a file's content."""
    if not os.path.exists(file_path):
        return default
    try:
        with open(file_path, "r") as f:
            return f.read().strip()
    except Exception as e:
        log(f"Error reading file {file_path}: {e}", "Utils")
        return default

def write_file(file_path, content):
    """Safely write content to a file, ensuring the directory exists."""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as f:
            f.write(content)
        return True
    except Exception as e:
        log(f"Error writing to file {file_path}: {e}", "Utils")
        return False

# --- Billing & ROI ---
def get_billing_data(project_dir="."):
    """Retrieve billing data from .jbot/billing.json."""
    billing_path = os.path.join(project_dir, ".jbot/billing.json")
    return load_json(billing_path, default={"total_cost": 0.0, "currency": "USD"})

def update_billing_data(project_dir=".", run_cost=0.01):
    """Increment the total cost in .jbot/billing.json."""
    billing_path = os.path.join(project_dir, ".jbot/billing.json")
    data = get_billing_data(project_dir)
    data["total_cost"] = data.get("total_cost", 0.0) + run_cost
    save_json(billing_path, data)
    return data

# --- Tasks ---
def parse_tasks(tasks_path):
    """Parses TASKS.md into sections and extracted data."""
    data = {
        "active": [], 
        "done_count": 0, 
        "backlog": [], 
        "vision": "",
        "sections": {
            "header": [],
            "vision": [],
            "active": [],
            "backlog": [],
            "completed": [],
        }
    }
    if not os.path.exists(tasks_path):
        return data

    with open(tasks_path, "r") as f:
        lines = f.readlines()
        current_section = "header"
        for line in lines:
            if "## Strategic Vision" in line:
                current_section = "vision"
            elif "## Active Tasks" in line:
                current_section = "active"
            elif "## Backlog" in line:
                current_section = "backlog"
            elif "## Completed Tasks" in line:
                current_section = "completed"
            
            data["sections"][current_section].append(line)

            if current_section == "vision" and not line.startswith("##"):
                data["vision"] += line
            elif current_section == "active" and line.strip().startswith("- [ ]"):
                data["active"].append(line.strip())
            elif current_section == "backlog" and line.strip().startswith("- [ ]"):
                data["backlog"].append(line.strip())
            
            if line.strip().startswith("- [x]"):
                data["done_count"] += 1
    
    data["vision"] = data["vision"].strip()
    return data

def add_task(tasks_path, task_text, agent=None):
    """Adds a new task to the Active Tasks section of TASKS.md."""
    if not os.path.exists(tasks_path):
        log(f"Tasks file {tasks_path} not found.", "Utils")
        return False

    with open(tasks_path, "r") as f:
        lines = f.readlines()

    new_lines = []
    added = False
    task_entry = f"- [ ] **{task_text}**"
    if agent:
        task_entry += f" (Agent: {agent})"
    task_entry += "\n"

    for line in lines:
        new_lines.append(line)
        if "## Active Tasks" in line and not added:
            new_lines.append(task_entry)
            added = True

    if not added:
        new_lines.append("\n## Active Tasks\n")
        new_lines.append(task_entry)

    with open(tasks_path, "w") as f:
        f.writelines(new_lines)
    return True

# --- Team & Registry ---
def get_team_registry(project_dir="."):
    """Load the team registry from .jbot/agents.json."""
    agents_path = os.path.join(project_dir, ".jbot/agents.json")
    return load_json(agents_path, default={})

# --- Messages ---
def get_recent_messages(msgs_dir, count=5, include_human=False):
    """Retrieve the most recent messages from the messages directory."""
    if not os.path.exists(msgs_dir):
        return []
    
    msg_files = sorted([
        f for f in os.listdir(msgs_dir) 
        if os.path.isfile(os.path.join(msgs_dir, f)) and (include_human or f != "human.txt")
    ])
    
    results = []
    for mf in msg_files[-count:]:
        try:
            with open(os.path.join(msgs_dir, mf), "r") as f:
                results.append({"filename": mf, "content": f.read()})
        except Exception:
            pass
    return results

# --- Memory & Logs ---
def get_recent_logs(log_path, count=10):
    """Retrieve recent entries from the memory log."""
    if not os.path.exists(log_path):
        return []
    
    entries = []
    try:
        with open(log_path, "r") as f:
            lines = f.readlines()
            for line in reversed(lines):
                if len(entries) >= count:
                    break
                try:
                    entries.append(json.loads(line))
                except Exception:
                    pass
    except Exception:
        pass
    return entries

# --- Directives ---
def parse_directives(dir_path):
    """Parse directives and filter out expired ones."""
    if not os.path.exists(dir_path):
        return []
    
    dir_files = sorted([
        f for f in os.listdir(dir_path) 
        if f.endswith((".txt", ".md")) and f != "README.md"
    ])
    
    valid_directives = []
    today = datetime.now().strftime("%Y-%m-%d")
    
    for df in dir_files:
        try:
            with open(os.path.join(dir_path, df), "r") as f:
                content = f.read()
                
                # Check expiration in content or filename
                is_expired = False
                content_exp_match = re.search(r"Expiration:\s*(\d{4}-\d{2}-\d{2})", content, re.IGNORECASE)
                filename_exp_match = re.search(r"(\d{4}-\d{2}-\d{2})", df)
                
                if content_exp_match:
                    if today > content_exp_match.group(1):
                        is_expired = True
                elif filename_exp_match:
                    if today > filename_exp_match.group(1):
                        is_expired = True
                
                if not is_expired:
                    valid_directives.append({"filename": df, "content": content})
        except Exception:
            pass
    return valid_directives
