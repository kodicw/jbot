import os
import re
import subprocess
from typing import Dict, Any, Optional
import jbot_core as core
import jbot_infra as infra


def _get_nb_tasks() -> str:
    """Helper to fetch task board content from nb."""
    return (
        infra.get_note_content("type:tasks")
        or "# JBot Task Board\n\n## Strategic Vision\n- Goal: Technical Excellence\n\n## Active Tasks\n\n## Backlog\n\n## Completed Tasks\n"
    )


def _push_nb_tasks(content: str) -> bool:
    """Helper to push updated task board back to nb."""
    env = os.environ.copy()
    env["EDITOR"] = "cat"
    if "NB_USER_NAME" not in env:
        env["NB_USER_NAME"] = "System (CLI)"

    try:
        subprocess.run(
            [
                "nb",
                "jbot:add",
                "--title",
                "Task Board",
                "--tags",
                "type:tasks",
                "--content",
                content,
                "--overwrite",
                "--force",
            ],
            check=True,
            capture_output=True,
            env=env,
        )
        return True
    except Exception as e:
        core.log(f"Error pushing tasks to nb: {e}", "Tasks")
        return False


def parse_tasks(tasks_path: str = "") -> Dict[str, Any]:
    """Parses the task board from a file or nb into sections and extracted data."""
    if tasks_path:
        if os.path.exists(tasks_path):
            content = core.read_file(tasks_path)
        else:
            # If path was provided but doesn't exist, return empty board
            return {
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
    else:
        # Pull from nb if path is empty
        content = _get_nb_tasks()

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

    lines = content.splitlines(keepends=True)
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
    """Adds a new task to the task board (local file or nb)."""
    if tasks_path and os.path.exists(tasks_path):
        content = core.read_file(tasks_path)
    else:
        content = _get_nb_tasks()

    lines = content.splitlines(keepends=True)

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

    final_content = "".join(new_lines)
    if tasks_path and os.path.exists(tasks_path):
        return core.write_file(tasks_path, final_content)
    else:
        return _push_nb_tasks(final_content)


def update_task(
    tasks_path: str,
    task_text_search: str,
    new_text: Optional[str] = None,
    agent: Optional[str] = None,
    move_to: Optional[str] = None,
) -> bool:
    """Updates a task in the task board (local file or nb)."""
    if tasks_path and os.path.exists(tasks_path):
        content = core.read_file(tasks_path)
    else:
        content = _get_nb_tasks()

    lines = content.splitlines(keepends=True)

    new_lines = []
    task_line_index = -1

    # Find the task
    for i, line in enumerate(lines):
        if "- [ ]" in line and task_text_search.lower() in line.lower():
            task_line_index = i
            break

    if task_line_index == -1:
        core.log(f"Task matching '{task_text_search}' not found.", "Tasks")
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
        final_content = "".join(new_lines)
    else:
        lines[task_line_index] = new_task_line
        final_content = "".join(lines)

    if tasks_path and os.path.exists(tasks_path):
        return core.write_file(tasks_path, final_content)
    else:
        return _push_nb_tasks(final_content)


def complete_task(tasks_path: str, task_text_search: str) -> bool:
    """Marks a task as completed in the task board (local file or nb)."""
    if tasks_path and os.path.exists(tasks_path):
        content = core.read_file(tasks_path)
    else:
        content = _get_nb_tasks()

    lines = content.splitlines(keepends=True)

    task_line_index = -1
    for i, line in enumerate(lines):
        if "- [ ]" in line and task_text_search.lower() in line.lower():
            task_line_index = i
            break

    if task_line_index == -1:
        core.log(f"Task matching '{task_text_search}' not found.", "Tasks")
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

    final_content = "".join(new_lines)
    if tasks_path and os.path.exists(tasks_path):
        return core.write_file(tasks_path, final_content)
    else:
        return _push_nb_tasks(final_content)
