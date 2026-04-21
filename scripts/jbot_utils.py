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


# --- Git ---
def is_git_clean(project_dir="."):
    """Check if the git workspace is clean."""
    try:
        result = subprocess.run(
            ["git", "-C", project_dir, "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True,
        )
        return len(result.stdout.strip()) == 0
    except Exception as e:
        log(f"Error checking git status: {e}", "Utils")
        return False


# --- Versioning ---
def get_version(project_dir="."):
    """Retrieve the current version from the VERSION file."""
    version_path = os.path.join(project_dir, "VERSION")
    return read_file(version_path, default="0.0.0")


def bump_version(project_dir=".", part="patch"):
    """Increment the version (major, minor, patch)."""
    current_version = get_version(project_dir)
    try:
        parts = list(map(int, current_version.split(".")))
        if len(parts) != 3:
            log(f"Invalid version format: {current_version}", "Utils")
            return None

        if part == "major":
            parts[0] += 1
            parts[1] = 0
            parts[2] = 0
        elif part == "minor":
            parts[1] += 1
            parts[2] = 0
        elif part == "patch":
            parts[2] += 1
        else:
            log(f"Invalid version part: {part}", "Utils")
            return None

        new_version = ".".join(map(str, parts))
        if write_file(os.path.join(project_dir, "VERSION"), new_version):
            return new_version
    except Exception as e:
        log(f"Error bumping version: {e}", "Utils")
    return None


def update_changelog(project_dir, new_version):
    """
    Updates CHANGELOG.md by moving content from the [Unreleased] section 
    to a new versioned section.
    """
    changelog_path = os.path.join(project_dir, "CHANGELOG.md")
    if not os.path.exists(changelog_path):
        log("CHANGELOG.md not found.", "Utils")
        return False

    with open(changelog_path, "r") as f:
        lines = f.readlines()

    unreleased_header = "## [Unreleased]"
    unreleased_index = -1
    next_version_index = -1
    today_date = datetime.now().strftime("%Y-%m-%d")

    # Locate the [Unreleased] section and the start of the next version section
    for i, line in enumerate(lines):
        if unreleased_header in line:
            unreleased_index = i
        elif unreleased_index != -1 and line.startswith("## [") and i > unreleased_index:
            next_version_index = i
            break

    if unreleased_index == -1:
        log("Could not find [Unreleased] section in CHANGELOG.md", "Utils")
        return False

    # If no next version section exists, unreleased content goes to the end of the file
    if next_version_index == -1:
        next_version_index = len(lines)

    # Extract the unreleased content (lines between unreleased header and next section)
    unreleased_content = lines[unreleased_index + 1 : next_version_index]

    # Check if there is actual meaningful change content beyond headers
    has_changes = any(
        line.strip() and not line.strip().startswith("###")
        for line in unreleased_content
    )
    if not has_changes:
        log("No meaningful changes found in [Unreleased] section.", "Utils")
        # We still proceed to create the version header, as bump was requested.

    # Reconstruct the changelog with a new empty [Unreleased] section
    # and the new versioned section containing the extracted content.
    updated_changelog = lines[: unreleased_index + 1]
    updated_changelog.append("\n")  # Empty line after [Unreleased] header
    updated_changelog.append(f"## [{new_version}] - {today_date}\n")
    updated_changelog.extend(unreleased_content)
    updated_changelog.extend(lines[next_version_index:])

    with open(changelog_path, "w") as f:
        f.writelines(updated_changelog)
    
    log(f"Updated CHANGELOG.md for version {new_version}.", "Utils")
    return True


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
        },
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


def add_task(tasks_path, task_text, agent=None, backlog=False):
    """Adds a new task to TASKS.md."""
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

    target_section = "## Backlog" if backlog else "## Active Tasks"

    for line in lines:
        new_lines.append(line)
        if target_section in line and not added:
            new_lines.append(task_entry)
            added = True

    if not added:
        new_lines.append(f"\n{target_section}\n")
        new_lines.append(task_entry)

    with open(tasks_path, "w") as f:
        f.writelines(new_lines)
    return True


def update_task(tasks_path, task_text_search, new_text=None, agent=None, move_to=None):
    """Updates a task in TASKS.md."""
    if not os.path.exists(tasks_path):
        log(f"Tasks file {tasks_path} not found.", "Utils")
        return False

    with open(tasks_path, "r") as f:
        lines = f.readlines()

    new_lines = []
    task_line_index = -1

    # Find the task
    for i, line in enumerate(lines):
        if "- [ ]" in line and task_text_search.lower() in line.lower():
            task_line_index = i
            break

    if task_line_index == -1:
        log(f"Task matching '{task_text_search}' not found.", "Utils")
        return False

    # Parse current task line
    current_line = lines[task_line_index]
    # Extract text from **...** or just after - [ ]
    match = re.search(r"\*\*([^*]+)\*\*", current_line)
    if match:
        text = match.group(1)
    else:
        # Match text between "- [ ]" and either "(Agent:" or end of line
        text_match = re.search(r"- \[ \]\s*(.*?)(?:\s*\(Agent:|\s*$)", current_line)
        text = text_match.group(1).strip() if text_match else task_text_search

    # Extract agent from (Agent: ...)
    agent_match = re.search(r"\(Agent:\s*([^)]+)\)", current_line)
    current_agent = agent_match.group(1) if agent_match else None

    # Update values
    final_text = new_text if new_text else text
    final_agent = agent if agent else current_agent

    new_task_line = f"- [ ] **{final_text}**"
    if final_agent:
        new_task_line += f" (Agent: {final_agent})"
    new_task_line += "\n"

    if move_to:
        # Remove from current position and move to target section
        lines.pop(task_line_index)
        target_header = "## Active Tasks" if move_to == "active" else "## Backlog"
        added = False
        for line in lines:
            new_lines.append(line)
            if target_header in line and not added:
                new_lines.append(new_task_line)
                added = True
        if not added:
            new_lines.append(f"\n{target_header}\n")
            new_lines.append(new_task_line)
    else:
        # Just replace the line
        lines[task_line_index] = new_task_line
        new_lines = lines

    with open(tasks_path, "w") as f:
        f.writelines(new_lines)
    return True


def complete_task(tasks_path, task_text_search):
    """Marks a task as completed and moves it to the Completed Tasks section."""
    if not os.path.exists(tasks_path):
        log(f"Tasks file {tasks_path} not found.", "Utils")
        return False

    with open(tasks_path, "r") as f:
        lines = f.readlines()

    task_line_index = -1
    for i, line in enumerate(lines):
        if "- [ ]" in line and task_text_search.lower() in line.lower():
            task_line_index = i
            break

    if task_line_index == -1:
        log(f"Task matching '{task_text_search}' not found.", "Utils")
        return False

    task_line = lines.pop(task_line_index)
    completed_line = task_line.replace("- [ ]", "- [x]")

    new_lines = []
    added = False
    for line in lines:
        new_lines.append(line)
        if "## Completed Tasks" in line and not added:
            new_lines.append(completed_line)
            added = True

    if not added:
        new_lines.append("\n## Completed Tasks\n")
        new_lines.append(completed_line)

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

    msg_files = sorted(
        [
            f
            for f in os.listdir(msgs_dir)
            if os.path.isfile(os.path.join(msgs_dir, f))
            and (include_human or f != "human.txt")
        ]
    )

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

    dir_files = sorted(
        [
            f
            for f in os.listdir(dir_path)
            if f.endswith((".txt", ".md")) and f != "README.md"
        ]
    )

    valid_directives = []
    today = datetime.now().strftime("%Y-%m-%d")

    for df in dir_files:
        try:
            with open(os.path.join(dir_path, df), "r") as f:
                content = f.read()

                # Check expiration in content or filename
                is_expired = False
                content_exp_match = re.search(
                    r"Expiration:\s*(\d{4}-\d{2}-\d{2})", content, re.IGNORECASE
                )
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
