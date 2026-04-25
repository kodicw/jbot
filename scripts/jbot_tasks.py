import re
from typing import Dict, Any, Optional

# Context: [[nb:jbot:adr-173]], [[nb:jbot:adr-193]]
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
    client = infra.NbClient()

    try:
        # Find the latest task board to update instead of creating a new one
        notes = client.ls(tags=["type:tasks"])
        if notes:
            # Sort by ID descending as a proxy for newest (higher ID = newer)
            notes.sort(key=lambda x: int(x.id), reverse=True)
            # Prefer Authoritative Task Board (198 or 5) if it exists, otherwise use latest
            target_id = None
            for n in notes:
                if n.id in ["198", "5"] or "Authoritative" in n.title:
                    target_id = n.id
                    break
            if not target_id:
                target_id = notes[0].id

            return client.edit(target_id, content, overwrite=True)
        else:
            # Create a new authoritative task board
            new_id = client.add(
                title="Authoritative Task Board (CEO)",
                content=content,
                tags=["type:tasks"],
            )
            return new_id is not None
    except Exception as e:
        core.log(f"Error pushing tasks to nb: {e}", "Tasks")
        return False


def parse_tasks() -> Dict[str, Any]:
    """Parses the task board from nb into sections and extracted data.

    Context: [[nb:jbot:adr-193]] - Robust Section Parsing
    """
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

    # Robust regex for section matching as per ADR [[nb:jbot:adr-193]]
    re_vision = re.compile(r"^##.*(vision|goal|strategic)", re.IGNORECASE)
    re_active = re.compile(r"^##.*active", re.IGNORECASE)
    re_backlog = re.compile(r"^##.*backlog", re.IGNORECASE)
    re_completed = re.compile(r"^##.*(completed|done)", re.IGNORECASE)

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("##"):
            if re_vision.search(stripped):
                current_section = "vision"
            elif re_active.search(stripped):
                current_section = "active"
            elif re_backlog.search(stripped):
                current_section = "backlog"
            elif re_completed.search(stripped):
                current_section = "completed"

        data["sections"][current_section].append(line)

        if current_section == "vision" and not stripped.startswith("##"):
            # Accumulate vision text, ignoring leading bullet points if they are just formatting
            vision_line = re.sub(r"^[-*]\s+", "", stripped)
            if vision_line:
                data["vision"] += vision_line + " "
        elif current_section == "active":
            if re.match(r"^\s*-\s*\[\s*\]", stripped):
                data["active"].append(stripped)
            elif re.match(r"^\s*-\s*\[[xX]\]", stripped):
                # Count [x] in active as done, but don't show in active dashboard list
                data["done_count"] += 1
        elif current_section == "backlog":
            if re.match(r"^\s*-\s*\[\s*\]", stripped) or (
                stripped.startswith("- ") and "[" not in stripped[:5]
            ):
                task_text = stripped
                if "[" not in task_text[:5]:
                    task_text = task_text.replace("- ", "- [ ] ", 1)
                data["backlog"].append(task_text)

        # done_count: Count everything in completed section, plus [x] anywhere else
        if current_section == "completed":
            if stripped.startswith("-"):
                data["done_count"] += 1
        elif (
            current_section != "active"
            and current_section != "completed"
            and re.search(r"-\s*\[[xX]\]", stripped)
        ):
            data["done_count"] += 1

    data["vision"] = data["vision"].strip()
    return data


def add_task(
    task_text: str, agent: Optional[str] = None, backlog: bool = False
) -> bool:
    """Adds a new task to the nb task board."""
    content = _get_nb_tasks()

    lines = content.splitlines(keepends=True)

    new_lines = []
    added = False
    task_entry = f"- [ ] **{task_text}**"
    if agent:
        task_entry += f" (Agent: {agent})"
    task_entry += "\n"

    target_section = "## Backlog" if backlog else "## Active Tasks"

    for i, line in enumerate(lines):
        if re.search(r"^##.*(Backlog|Active Tasks)", line, re.IGNORECASE):
            if ("backlog" in line.lower() and backlog) or (
                "active tasks" in line.lower() and not backlog
            ):
                new_lines.extend(lines[: i + 1])
                new_lines.append(task_entry)
                new_lines.extend(lines[i + 1 :])
                added = True
                break

    if not added:
        new_lines.append(f"\n{target_section}\n")
        new_lines.append(task_entry)

    final_content = "".join(new_lines)
    return _push_nb_tasks(final_content)


def update_task(
    task_text_search: str,
    new_text: Optional[str] = None,
    agent: Optional[str] = None,
    move_to: Optional[str] = None,
) -> bool:
    """Updates a task in the nb task board."""
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
        added = False
        for i, line in enumerate(lines):
            new_lines.append(line)
            if re.search(r"^##.*(Active Tasks|Backlog)", line, re.IGNORECASE):
                if (move_to == "active" and "active tasks" in line.lower()) or (
                    move_to == "backlog" and "backlog" in line.lower()
                ):
                    new_lines.append(new_task_line)
                    added = True
                    # Append the rest of the lines and break
                    new_lines.extend(lines[i + 1 :])
                    break
        if not added:
            new_lines.append(
                f"\n## {'Active Tasks' if move_to == 'active' else 'Backlog'}\n"
            )
            new_lines.append(new_task_line)
        final_content = "".join(new_lines)
    else:
        lines[task_line_index] = new_task_line
        final_content = "".join(lines)

    return _push_nb_tasks(final_content)


def complete_task(task_text_search: str) -> bool:
    """Marks a task as completed in the nb task board and moves it to the completed section."""
    content = _get_nb_tasks()

    lines = content.splitlines(keepends=True)

    task_line_index = -1
    for i, line in enumerate(lines):
        # Match task line regardless of whether it is already checked
        # Ignore common markdown formatting for matching
        line_clean = line.replace("`", "").replace("*", "").replace("_", "")
        if (
            re.search(r"- \[[ x]\]", line) or line.strip().startswith("- ")
        ) and task_text_search.lower() in line_clean.lower():
            task_line_index = i
            break

    if task_line_index == -1:
        core.log(f"Task matching '{task_text_search}' not found.", "Tasks")
        return False

    task_line = lines.pop(task_line_index)
    # Ensure it's marked as [x]
    completed_line = re.sub(r"- \[[ x]\]", "- [x]", task_line)

    new_lines = []
    added = False
    re_completed = re.compile(r"^##.*(completed|done)", re.IGNORECASE)

    for i, line in enumerate(lines):
        new_lines.append(line)
        if re_completed.search(line) and not added:
            new_lines.append(completed_line)
            added = True
            # Note: We continue to add the rest of the lines

    # If we haven't found a completed section, add one
    if not added:
        new_lines.append("\n## ✅ Completed Tasks\n")
        new_lines.append(completed_line)

    final_content = "".join(new_lines)
    return _push_nb_tasks(final_content)
