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


def purge_directives(dir_path, archive_path):
    """Archives expired directives from dir_path to archive_path."""
    if not os.path.exists(dir_path):
        log(f"Error: Directive directory {dir_path} not found.", "Purge")
        return 0

    os.makedirs(archive_path, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    purged_count = 0

    dir_files = [
        f
        for f in os.listdir(dir_path)
        if f.endswith((".txt", ".md")) and f != "README.md"
    ]

    import shutil

    for df in dir_files:
        is_expired = False
        df_path = os.path.join(dir_path, df)

        if os.path.isdir(df_path):
            continue

        # Try to find a date (YYYY-MM-DD) in the filename
        date_match = re.search(r"(\d{4}-\d{2}-\d{2})", df)
        exp_date_from_filename = date_match.group(1) if date_match else None

        try:
            directive_content = read_file(df_path)
            if not directive_content:
                continue

            # Check for explicit expiration in content: "Expiration: YYYY-MM-DD"
            content_exp_match = re.search(
                r"Expiration:\s*(\d{4}-\d{2}-\d{2})",
                directive_content,
                re.IGNORECASE,
            )
            if content_exp_match:
                exp_date = content_exp_match.group(1)
                if today > exp_date:
                    is_expired = True
                    log(
                        f"Directive {df} has expired (from content: {exp_date}).",
                        "Purge",
                    )
            elif exp_date_from_filename:
                if today > exp_date_from_filename:
                    is_expired = True
                    log(
                        f"Directive {df} has expired (from filename: {exp_date_from_filename}).",
                        "Purge",
                    )

            if is_expired:
                dest_path = os.path.join(archive_path, df)
                if os.path.exists(dest_path):
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    name, ext = os.path.splitext(df)
                    dest_path = os.path.join(archive_path, f"{name}_{timestamp}{ext}")

                shutil.move(df_path, dest_path)
                log(
                    f"Archived expired directive: {df} -> {os.path.basename(dest_path)}",
                    "Purge",
                )
                purged_count += 1

        except Exception as e:
            log(f"Error processing directive {df}: {e}", "Purge")

    return purged_count


def rotate_memory(memory_log, archive_log, limit=100):
    """Rotates the memory log, moving older entries to archive."""
    if not os.path.exists(memory_log):
        log(f"Memory log {memory_log} not found. Skipping rotation.", "Rotate")
        return False

    try:
        with open(memory_log, "r") as f:
            lines = f.readlines()

        if len(lines) <= limit:
            return False

        # Split lines
        to_keep = lines[-limit:]
        to_archive = lines[:-limit]

        log(
            f"Rotating memory: Keeping {len(to_keep)} entries, Archiving {len(to_archive)} entries.",
            "Rotate",
        )

        # Append to archive
        with open(archive_log, "a") as f:
            f.writelines(to_archive)

        # Rewrite memory log
        with open(memory_log, "w") as f:
            f.writelines(to_keep)

        return True
    except Exception as e:
        log(f"Error rotating memory log: {e}", "Rotate")
        return False


def rotate_tasks(tasks_file="TASKS.md", archive_file="TASKS.archive.md", limit=20):
    """Rotates the task board, moving completed tasks to archive."""
    if not os.path.exists(tasks_file):
        log(f"Tasks file {tasks_file} not found.", "Rotate")
        return False

    try:
        tasks_data = parse_tasks(tasks_file)
        sections = tasks_data["sections"]

        # Ensure headers exist
        if not sections["vision"]:
            sections["vision"] = ["## Strategic Vision (CEO)\n"]
        if not sections["active"]:
            sections["active"] = ["## Active Tasks\n"]
        if not sections["backlog"]:
            sections["backlog"] = ["## Backlog\n"]
        if not sections["completed"]:
            sections["completed"] = ["## Completed Tasks\n"]

        new_active = [sections["active"][0]]
        new_backlog = [sections["backlog"][0]]
        newly_completed = []

        for line in sections["active"][1:]:
            if "[x]" in line:
                newly_completed.append(line)
            elif line.strip() in ("", "..."):
                continue
            else:
                new_active.append(line)

        for line in sections["backlog"][1:]:
            if "[x]" in line:
                newly_completed.append(line)
            elif line.strip() in ("", "..."):
                continue
            else:
                new_backlog.append(line)

        current_completed = [
            line for line in sections["completed"][1:] if line.strip() != "..."
        ]
        all_completed = current_completed + newly_completed

        to_keep = all_completed
        to_archive = []

        if len(all_completed) > limit:
            to_keep = all_completed[-limit:]
            to_archive = all_completed[:-limit]
            log(f"Archiving {len(to_archive)} completed tasks.", "Rotate")

        if to_archive:
            if not os.path.exists(archive_file) or os.path.getsize(archive_file) == 0:
                write_file(archive_file, "# JBot Task Archive\n\n")
            with open(archive_file, "a") as f:
                f.write(f"## Archived on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.writelines(to_archive)
                f.write("\n")

        with open(tasks_file, "w") as f:
            f.writelines(sections["header"] if sections["header"] else ["# JBot Task Board\n\n"])
            f.writelines(sections["vision"])
            f.write("\n")
            f.writelines(new_active)
            if not new_active[-1].endswith("\n"): f.write("\n")
            f.write("\n")
            f.writelines(new_backlog)
            if not new_backlog[-1].endswith("\n"): f.write("\n")
            f.write("\n")
            f.writelines(sections["completed"][:1])
            f.writelines(to_keep)

        return True
    except Exception as e:
        log(f"Error rotating tasks: {e}", "Rotate")
        return False


def rotate_messages(msg_dir, archive_dir, limit=50):
    """Archives older messages from msg_dir to archive_dir."""
    if not os.path.exists(msg_dir):
        log(f"Message directory {msg_dir} not found.", "Rotate")
        return False

    os.makedirs(archive_dir, exist_ok=True)
    
    msg_files = sorted([
        f for f in os.listdir(msg_dir)
        if os.path.isfile(os.path.join(msg_dir, f)) and f != "human.txt"
    ])

    if len(msg_files) <= limit:
        return False

    to_archive = msg_files[:-limit]
    log(f"Archiving {len(to_archive)} messages.", "Rotate")

    import shutil
    for mf in to_archive:
        shutil.move(os.path.join(msg_dir, mf), os.path.join(archive_dir, mf))

    return True


def generate_dashboard(output_file="INDEX.md", project_dir="."):
    """Generates a markdown dashboard summarizing the project status."""
    dashboard_content = "# JBot Dashboard\n\n"
    dashboard_content += (
        f"*Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
    )

    # Find core files upwards
    goal_path = find_file_upwards(".project_goal", project_dir)
    tasks_path = find_file_upwards("TASKS.md", project_dir)
    changelog_path = find_file_upwards("CHANGELOG.md", project_dir)

    # 1. Company Vision
    dashboard_content += "## 🎯 Company Vision\n"
    if goal_path and os.path.exists(goal_path):
        with open(goal_path, "r") as f:
            dashboard_content += f"> {f.read().strip()}\n\n"
    else:
        dashboard_content += "No current vision defined.\n\n"

    # 2. Team Roster
    dashboard_content += "## 👥 Team Roster\n"
    agents = get_team_registry(project_dir)
    if agents:
        dashboard_content += "| Agent | Role | Description |\n"
        dashboard_content += "|-------|------|-------------|\n"
        for name, info in agents.items():
            dashboard_content += (
                f"| {name} | {info.get('role')} | {info.get('description')} |\n"
            )
        dashboard_content += "\n"
    else:
        dashboard_content += "No team registry found.\n\n"

    # 3. Active Tasks
    dashboard_content += "## 🚀 Active Tasks\n"
    tasks_data = (
        parse_tasks(tasks_path) if tasks_path else {"active": [], "done_count": 0}
    )
    if tasks_data["active"]:
        for task in tasks_data["active"][:10]:
            dashboard_content += f"{task}\n"
        dashboard_content += "\n"
    else:
        dashboard_content += "No active tasks.\n\n"

    # 4. Status & Progress
    dashboard_content += "## 📈 Status & Progress\n"

    # Milestone count from changelog
    milestone_count = 0
    if changelog_path and os.path.exists(changelog_path):
        with open(changelog_path, "r") as f:
            for line in f:
                if line.strip().startswith("- **"):
                    milestone_count += 1

    dashboard_content += f"- **Tasks Completed:** {tasks_data['done_count']}\n"
    dashboard_content += f"- **Milestones Achieved:** {milestone_count}\n\n"

    # 5. Recent Milestones
    dashboard_content += "## 🏆 Recent Milestones\n"
    if changelog_path and os.path.exists(changelog_path):
        with open(changelog_path, "r") as f:
            lines = f.readlines()
            milestones = [
                line.strip() for line in lines if line.strip().startswith("- **")
            ]
            for m in milestones[:5]:
                dashboard_content += f"{m}\n"
            dashboard_content += "\n"
    else:
        dashboard_content += "No changelog found.\n\n"

    with open(os.path.join(project_dir, output_file), "w") as f:
        f.write(dashboard_content)

    log(f"Dashboard generated successfully: {output_file}", "Dashboard")
    return True


def send_message(to_dir, agent_name, body, subject="No Subject"):
    """Sends a message to the specified project directory."""
    msgs_dir = os.path.join(to_dir, ".jbot", "messages")
    if not os.path.exists(msgs_dir):
        log(f"Error: Messages directory {msgs_dir} not found.", "Messaging")
        return False

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{timestamp}_{agent_name}.txt"
    file_path = os.path.join(msgs_dir, filename)

    message_content = f"To: all\nFrom: {agent_name}\nSubject: {subject}\n\n{body}\n"

    try:
        with open(file_path, "w") as f:
            f.write(message_content)
        log(f"Message sent: {filename}", "Messaging")
        return True
    except Exception as e:
        log(f"Error sending message: {e}", "Messaging")
        return False


def run_maintenance(project_dir):
    """Performs all automated infrastructure maintenance tasks."""
    log("Starting infrastructure maintenance...", "Maintenance")

    # 0. Infrastructure Initialization
    for d in [
        ".jbot/queues",
        ".jbot/messages",
        ".jbot/directives",
        ".jbot/messages/archive",
        ".jbot/directives/archive",
    ]:
        dir_path = os.path.join(project_dir, d)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            log(f"Initialized directory: {d}", "Maintenance")

    # 1. Memory Consolidation
    queues_dir = os.path.join(project_dir, ".jbot/queues")
    memory_log = os.path.join(project_dir, ".jbot/memory.log")
    if os.path.exists(queues_dir):
        for q_file in os.listdir(queues_dir):
            if q_file.endswith(".json"):
                q_path = os.path.join(queues_dir, q_file)
                agent_name = q_file[:-5]
                log(f"Consolidating memory from {agent_name}...", "Maintenance")
                try:
                    content = load_json(q_path)
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
                    log(f"Error consolidating {q_path}: {e}", "Maintenance")

    # 2. Automated Purging
    purge_directives(
        os.path.join(project_dir, ".jbot/directives"),
        os.path.join(project_dir, ".jbot/directives/archive"),
    )

    # 3. Automated Rotation
    rotate_memory(
        os.path.join(project_dir, ".jbot/memory.log"),
        os.path.join(project_dir, ".jbot/memory.log.archive"),
    )

    # 4. Dashboard Generation
    generate_dashboard(project_dir=project_dir)

    log("Maintenance complete.", "Maintenance")
    return True
