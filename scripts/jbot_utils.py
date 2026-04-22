import os
import json
import re
import subprocess
import sys
from datetime import datetime
import jbot_rotation


from typing import List, Dict, Any, Optional


# --- Logging ---
def log(msg: str, component: str = "JBot") -> None:
    """Standardized logging format for all JBot scripts."""
    print(f"[{datetime.now()}] {component}: {msg}")


# --- Paths & Files ---
def find_file_upwards(filename: str, start_dir: str = ".") -> Optional[str]:
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


def get_project_root(start_dir: str = ".") -> str:
    """Find the project root by looking for .project_goal."""
    goal_path = find_file_upwards(".project_goal", start_dir)
    if goal_path:
        return os.path.dirname(goal_path)
    return os.path.abspath(start_dir)


def load_json(file_path: str, default: Any = None) -> Any:
    """Safely load a JSON file."""
    if not os.path.exists(file_path):
        return default if default is not None else {}
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except Exception as e:
        log(f"Error loading JSON from {file_path}: {e}", "Utils")
        return default if default is not None else {}


def save_json(file_path: str, data: Any) -> None:
    """Safely save a JSON file, ensuring the directory exists."""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        log(f"Error saving JSON to {file_path}: {e}", "Utils")


def read_file(file_path: str, default: str = "") -> str:
    """Safely read a file's content."""
    if not os.path.exists(file_path):
        return default
    try:
        with open(file_path, "r") as f:
            return f.read().strip()
    except Exception as e:
        log(f"Error reading file {file_path}: {e}", "Utils")
        return default


def write_file(file_path: str, content: str) -> bool:
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
def is_git_clean(project_dir: str = ".") -> bool:
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
def get_version(project_dir: str = ".") -> str:
    """Retrieve the current version from the VERSION file."""
    version_path = os.path.join(project_dir, "VERSION")
    return read_file(version_path, default="0.0.0")


def bump_version(project_dir: str = ".", part: str = "patch") -> Optional[str]:
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


def update_changelog(project_dir: str, new_version: str) -> bool:
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
        elif (
            unreleased_index != -1 and line.startswith("## [") and i > unreleased_index
        ):
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
def parse_tasks(tasks_path: str) -> Dict[str, Any]:
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


def add_task(
    tasks_path: str, task_text: str, agent: Optional[str] = None, backlog: bool = False
) -> bool:
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


def update_task(
    tasks_path: str,
    task_text_search: str,
    new_text: Optional[str] = None,
    agent: Optional[str] = None,
    move_to: Optional[str] = None,
) -> bool:
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
    match = re.search(r"\*\*([^*]+)\*\*", current_line)
    if match:
        text = match.group(1)
    else:
        text_match = re.search(r"- \[ \]\s*(.*?)(?:\s*\(Agent:|\s*$)", current_line)
        text = text_match.group(1).strip() if text_match else task_text_search

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
        lines[task_line_index] = new_task_line
        new_lines = lines

    with open(tasks_path, "w") as f:
        f.writelines(new_lines)
    return True


def complete_task(tasks_path: str, task_text_search: str) -> bool:
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
def get_team_registry(project_dir: str = ".") -> Dict[str, Any]:
    """Load the team registry from .jbot/agents.json."""
    agents_path = os.path.join(project_dir, ".jbot/agents.json")
    return load_json(agents_path, default={})


# --- Messages ---
def get_recent_messages(
    msgs_dir: str, count: int = 5, include_human: bool = False
) -> List[Dict[str, str]]:
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
def get_recent_logs(log_path: str, count: int = 10) -> List[Dict[str, Any]]:
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
def parse_directives(dir_path: str) -> List[Dict[str, str]]:
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


def generate_dashboard(output_file: str = "INDEX.md", project_dir: str = ".") -> bool:
    """Generates a markdown dashboard summarizing the project status."""
    dashboard_content = "# JBot Dashboard\n\n"
    dashboard_content += (
        f"*Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
    )

    goal_path = find_file_upwards(".project_goal", project_dir)
    tasks_path = find_file_upwards("TASKS.md", project_dir)
    changelog_path = find_file_upwards("CHANGELOG.md", project_dir)

    dashboard_content += "## 🎯 Company Vision\n"
    if goal_path and os.path.exists(goal_path):
        dashboard_content += f"> {read_file(goal_path)}\n\n"
    else:
        dashboard_content += "No current vision defined.\n\n"

    dashboard_content += "## 👥 Team Roster\n"
    agents = get_team_registry(project_dir)
    if agents:
        dashboard_content += (
            "| Agent | Role | Description |\n|-------|------|-------------|\n"
        )
        for name, info in agents.items():
            dashboard_content += (
                f"| {name} | {info.get('role')} | {info.get('description')} |\n"
            )
        dashboard_content += "\n"

    dashboard_content += "## 🚀 Active Tasks\n"
    tasks_data = (
        parse_tasks(tasks_path) if tasks_path else {"active": [], "done_count": 0}
    )
    if tasks_data["active"]:
        for task in tasks_data["active"][:10]:
            dashboard_content += f"{task}\n"
        dashboard_content += "\n"

    dashboard_content += "## 📈 Status & Progress\n"
    milestone_count = 0
    if changelog_path and os.path.exists(changelog_path):
        with open(changelog_path, "r") as f:
            milestone_count = sum(1 for line in f if line.strip().startswith("- **"))

    dashboard_content += f"- **Tasks Completed:** {tasks_data['done_count']}\n"
    dashboard_content += f"- **Milestones Achieved:** {milestone_count}\n\n"

    dashboard_content += "## 🏆 Recent Milestones\n"
    if changelog_path and os.path.exists(changelog_path):
        with open(changelog_path, "r") as f:
            milestones = [line.strip() for line in f if line.strip().startswith("- **")]
            for m in milestones[:5]:
                dashboard_content += f"{m}\n"
            dashboard_content += "\n"

    with open(os.path.join(project_dir, output_file), "w") as f:
        f.write(dashboard_content)
    return True


def send_message(
    to_dir: str, agent_name: str, body: str, subject: str = "No Subject"
) -> bool:
    """
    Sends a message. In the stateless model, messages are written to '.jbot/outbox'
    and consolidated by the maintenance service to avoid cross-agent state corruption.
    """
    outbox_dir = os.path.join(to_dir, ".jbot", "outbox")
    # In sandbox, outbox should already be initialized and bind-mounted as writeable.
    if not os.path.exists(outbox_dir):
        os.makedirs(outbox_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    # Using microsecond for extra uniqueness in case of rapid sends
    microsecond = datetime.now().strftime("%f")
    filename = f"{timestamp}_{microsecond}_{agent_name}.txt"
    file_path = os.path.join(outbox_dir, filename)

    message_content = f"To: all\nFrom: {agent_name}\nSubject: {subject}\n\n{body}\n"
    return write_file(file_path, message_content)


def initialize_infrastructure(project_dir: str) -> None:
    """Ensures all required JBot infrastructure directories exist."""
    infra_dirs = [
        ".jbot/queues",
        ".jbot/messages",
        ".jbot/directives",
        ".jbot/outbox",
        ".jbot/messages/archive",
        ".jbot/directives/archive",
    ]
    for d in infra_dirs:
        os.makedirs(os.path.join(project_dir, d), exist_ok=True)


def consolidate_messages(project_dir: str) -> None:
    """Moves messages from agent outboxes to the centralized message directory."""
    import shutil

    outbox_dir = os.path.join(project_dir, ".jbot/outbox")
    messages_dir = os.path.join(project_dir, ".jbot/messages")

    if not os.path.exists(outbox_dir):
        return

    for msg_file in os.listdir(outbox_dir):
        if msg_file.endswith(".txt"):
            try:
                shutil.move(
                    os.path.join(outbox_dir, msg_file),
                    os.path.join(messages_dir, msg_file),
                )
                log(f"Consolidated message: {msg_file}", "Maintenance")
            except Exception as e:
                log(f"Error consolidating message {msg_file}: {e}", "Maintenance")


def consolidate_memory(project_dir: str) -> None:
    """Aggregates agent memory queues into the central memory log."""
    queues_dir = os.path.join(project_dir, ".jbot/queues")
    memory_log = os.path.join(project_dir, ".jbot/memory.log")

    if not os.path.exists(queues_dir):
        return

    for q_file in os.listdir(queues_dir):
        if q_file.endswith(".json"):
            q_path = os.path.join(queues_dir, q_file)
            agent_name = q_file[:-5]
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
                log(f"Consolidated memory for {agent_name}", "Maintenance")
            except Exception as e:
                log(f"Error consolidating memory for {agent_name}: {e}", "Maintenance")


def run_maintenance(project_dir: str) -> bool:
    """
    Performs all automated infrastructure maintenance tasks.
    This is the central authority for infrastructure state changes.
    """
    log("Starting infrastructure maintenance...", "Maintenance")

    try:
        initialize_infrastructure(project_dir)
        consolidate_messages(project_dir)
        consolidate_memory(project_dir)
        jbot_rotation.perform_rotations(project_dir)
        generate_dashboard(project_dir=project_dir)
        log("Maintenance complete.", "Maintenance")
        return True
    except Exception as e:
        log(f"Maintenance failed: {e}", "Maintenance")
        return False


# --- Agent Execution ---
def assemble_context(
    agent_name: str,
    agent_role: str,
    agent_desc: str,
    project_dir: str,
    prompt_file: str,
) -> str:
    """
    Assembles the full context for the agent by reading various infrastructure files.
    """
    # Find key project files
    tasks_path = find_file_upwards("TASKS.md", project_dir) or "TASKS.md"
    goal_path = find_file_upwards(".project_goal", project_dir) or ".project_goal"

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

    goal = read_file(goal_path, "Maintain and improve the JBot project infrastructure.")

    # Memory / RAG (Shared History)
    logs = get_recent_logs(os.path.join(project_dir, ".jbot/memory.log"), 10)
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

    task_board = read_file(
        tasks_path,
        f"No Task Board found at {tasks_path}. Please initialize it if needed.",
    )

    # Team Registry
    agents = get_team_registry(project_dir)
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
        human_input = f"--- HUMAN FEEDBACK/DIRECTIVE ---\n{read_file(human_file)}\n--- END HUMAN FEEDBACK ---"
        log("Injected human feedback from human.txt", agent_name)

    recent_msgs = get_recent_messages(msgs_dir, 5)
    messages = (
        "\n".join(
            [f"--- Message {m['filename']} ---\n{m['content']}" for m in recent_msgs]
        )
        if recent_msgs
        else "No recent messages."
    )

    # Directives (Formal Laws)
    dir_list = parse_directives(os.path.join(project_dir, ".jbot/directives"))
    directives = (
        "\n".join(
            [f"--- Directive {d['filename']} ---\n{d['content']}" for d in dir_list]
        )
        if dir_list
        else "No formal directives."
    )

    # Prompt Preparation
    prompt_content = read_file(prompt_file)
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
    """Main execution logic for a JBot Agent (Stateless)."""
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

    os.chdir(project_dir)
    log(f"Starting stateless execution loop as {role}...", name)

    # Verify write access to outbox and queues (Stateless Mandate)
    queues_dir = ".jbot/queues"
    outbox_dir = ".jbot/outbox"
    for d in [queues_dir, outbox_dir]:
        if not os.access(d, os.W_OK):
            log(
                f"WARNING: Directory {d} is NOT writable. Agent state may not be persisted.",
                name,
            )

    # Assemble context
    prompt_content = assemble_context(name, role, description, project_dir, prompt_file)

    # Set up memory output for gemini (Redirects agent memory to a queue file)
    os.environ["MEMORY_OUTPUT"] = f"{queues_dir}/{name}.json"

    log("Invoking Gemini CLI...", name)

    # Execution (Gemini CLI runs in the background and writes its memory to MEMORY_OUTPUT)
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
            log(
                f"Error: Gemini CLI failed with exit code {process.returncode}",
                name,
            )
            sys.exit(process.returncode)

        # Final Verification (Verification of Agent's Output)
        pre_commit_script = os.path.join(project_dir, ".githooks/pre-commit")
        if os.path.exists(pre_commit_script):
            try:
                log("Running final output verification...", name)
                subprocess.run(["bash", pre_commit_script], check=True)
            except Exception as e:
                log(f"WARNING: Verification failed: {e}", name)

    except Exception as e:
        log(f"Error: Execution failed: {e}", name)
        sys.exit(1)

    log("Stateless execution loop finished.", name)
