import os
import re
import glob
from datetime import datetime
from typing import List, Dict, Optional

import jbot_core as core
import jbot_tasks as tasks
from jbot_memory_interface import get_memory_client

# Context: [[nb:jbot:adr-210]], [[nb:jbot:adr-193]]


def update_note_stably(title: str, content: str, tags: List[str]) -> bool:
    """Updates an existing note if found by title and tags, otherwise adds a new one."""
    client = get_memory_client()
    try:
        notes = client.ls(tags=tags)
        target_id = None
        for n in notes:
            if n.title.lower() == title.lower():
                target_id = n.id
                break

        if target_id:
            return client.edit(target_id, content)
        else:
            return client.add(title, content, tags=tags) is not None
    except Exception as e:
        core.log(f"Error stably updating note '{title}': {e}", "Utils")
        return False


def get_recent_adrs(count: int = 5) -> List[Dict[str, str]]:
    """Retrieve the most recent ADRs from the nb knowledge base."""
    try:
        client = get_memory_client()
        notes = client.ls(tags=["type:adr"])
        notes.sort(key=lambda x: int(x.id), reverse=True)

        results = []
        for note in notes:
            results.append({"id": note.id, "title": note.title})
            if len(results) >= count:
                break
        return results
    except Exception as e:
        core.log(f"Error fetching ADRs from nb: {e}", "Utils")
        return []


def get_directive_expiration(
    content: str, filename: Optional[str] = None
) -> Optional[str]:
    """Extracts expiration date from content or filename."""
    # 1. Check content for "Expiration: YYYY-MM-DD"
    content_exp_match = re.search(
        r"Expiration:\s*(\d{4}-\d{2}-\d{2})", content, re.IGNORECASE
    )
    if content_exp_match:
        return content_exp_match.group(1)

    # 2. Check filename for "YYYY-MM-DD"
    if filename:
        filename_exp_match = re.search(r"(\d{4}-\d{2}-\d{2})", filename)
        if filename_exp_match:
            return filename_exp_match.group(1)

    return None


def is_directive_expired(content: str, filename: Optional[str] = None) -> bool:
    """Checks if a directive is expired based on today's date."""
    exp_date = get_directive_expiration(content, filename)
    if not exp_date:
        return False

    today = datetime.now().strftime("%Y-%m-%d")
    return today > exp_date


def generate_dashboard(output_file: str = "INDEX.md", project_dir: str = ".") -> bool:
    """Generates a markdown dashboard summarizing the project status.

    Context: [[nb:jbot:adr-193]], [[nb:jbot:adr-200]], [[nb:jbot:adr-205]]
    """
    import jbot_infra as infra

    dashboard_content = "# JBot Dashboard\n\n"
    dashboard_content += (
        f"*Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
    )

    try:
        tasks_data = tasks.parse_tasks()
    except Exception as e:
        core.log(f"Error parsing tasks for dashboard: {e}", "Utils")
        tasks_data = {
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

    dashboard_content += "## 🎯 Strategic Vision\n"
    vision = infra.get_vision(project_dir)
    dashboard_content += f"> {vision}\n\n"

    dashboard_content += "## 👥 Team Roster\n"
    agents = infra.get_team_registry(project_dir)
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
    active_tasks = [t for t in tasks_data["active"] if "- [ ]" in t]
    if active_tasks:
        for task in active_tasks[:10]:
            match = re.search(r"\(Agent:\s*([^)]+)\)", task)
            agent_str = f" [{match.group(1)}]" if match else ""
            task_clean = re.sub(r"\s*\(Agent:\s*[^)]+\)", "", task)
            dashboard_content += f"{task_clean}{agent_str}\n"
        dashboard_content += "\n"
    else:
        dashboard_content += "No active tasks.\n\n"

    if tasks_data["backlog"]:
        dashboard_content += "## 📦 Backlog Highlights\n"
        for task in tasks_data["backlog"][:5]:
            dashboard_content += f"{task}\n"
        dashboard_content += "\n"

    completed_tasks = []
    for line in tasks_data["sections"]["completed"]:
        stripped = line.strip()
        if stripped.startswith("-"):
            completed_tasks.append(stripped)

    if completed_tasks:
        dashboard_content += "## ✅ Recently Completed\n"
        for task in completed_tasks[:5]:
            dashboard_content += f"{task}\n"
        dashboard_content += "\n"

    dashboard_content += "## 📜 Recent ADRs\n"
    adrs = get_recent_adrs(5)
    if adrs:
        for adr in adrs:
            dashboard_content += f"- [[nb:{adr['id']}]] {adr['title']}\n"
        dashboard_content += "\n"
    else:
        dashboard_content += "No ADRs found.\n\n"

    dashboard_content += "## 💬 Recent Messages\n"
    msgs_dir = os.path.join(project_dir, ".jbot/messages")
    recent_msgs = infra.get_recent_messages(msgs_dir, 5)
    if recent_msgs:
        for m in reversed(recent_msgs):
            headers = infra.parse_message_headers(m["content"])
            dashboard_content += f"- **[{headers['from']}]** {headers['subject']} ([{m['filename']}](.jbot/messages/{m['filename']}))\n"
        dashboard_content += "\n"
    else:
        dashboard_content += "No recent messages.\n\n"

    dashboard_content += "## 📊 Architectural Diagrams\n"
    mermaid_files = glob.glob(os.path.join(project_dir, "scripts/*.mermaid"))
    if mermaid_files:
        for mermaid_file in sorted(mermaid_files):
            title = (
                os.path.basename(mermaid_file)
                .replace(".mermaid", "")
                .replace("_", " ")
                .title()
            )
            content = core.read_file(mermaid_file)
            dashboard_content += f"### {title}\n"
            dashboard_content += "```mermaid\n"
            dashboard_content += content + "\n"
            dashboard_content += "```\n\n"

    dashboard_content += "## 📈 Status & Progress\n"
    changelog_path = core.find_file_upwards("CHANGELOG.md", project_dir)
    milestone_count = 0
    if changelog_path and os.path.exists(changelog_path):
        with open(changelog_path, "r") as f:
            milestone_count = sum(1 for line in f if line.strip().startswith("- **"))

    dashboard_content += f"- **Tasks Completed:** {tasks_data['done_count']}\n"
    dashboard_content += f"- **Milestones Achieved:** {milestone_count}\n\n"

    try:
        client = get_memory_client()
        all_notes = client.ls()
        adr_notes = client.ls(tags=["type:adr"])
        kb_total = len(all_notes)
        adr_total = len(adr_notes)

        velocity = (
            tasks_data["done_count"] / milestone_count if milestone_count > 0 else 0
        )
        density = adr_total / milestone_count if milestone_count > 0 else adr_total
        total_tasks = (
            len(tasks_data["active"])
            + len(tasks_data["backlog"])
            + tasks_data["done_count"]
        )
        completion_ratio = (
            (tasks_data["done_count"] / total_tasks * 100) if total_tasks > 0 else 0
        )

        dashboard_content += "### 📊 Technical ROI (Engineering Metrics)\n"
        dashboard_content += (
            f"- **Engineering Velocity:** {velocity:.2f} tasks/milestone\n"
        )
        dashboard_content += (
            f"- **Architectural Density:** {density:.2f} ADRs/milestone\n"
        )
        dashboard_content += f"- **Knowledge Base Growth:** {kb_total} records\n"
        dashboard_content += f"- **Completion Ratio:** {completion_ratio:.1f}%\n\n"
    except Exception as e:
        core.log(f"Error calculating Technical ROI: {e}", "Utils")

    dashboard_content += "## ✅ Recent Milestones\n"
    if changelog_path and os.path.exists(changelog_path):
        with open(changelog_path, "r") as f:
            milestones = [line.strip() for line in f if line.strip().startswith("- **")]
            for m in milestones[:5]:
                dashboard_content += f"{m}\n"
            dashboard_content += "\n"

    with open(os.path.join(project_dir, output_file), "w") as f:
        f.write(dashboard_content)
    return True
