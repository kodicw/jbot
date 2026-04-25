import os
import json
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
import jbot_core as core
import jbot_rotation
from nb_client import NbClient


# --- NB Stability Helpers ---
def update_note_stably(title: str, content: str, tags: List[str]) -> bool:
    """Updates an existing note if found by title and tags, otherwise adds a new one."""
    client = NbClient()
    try:
        # Find existing notes with these tags
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
        core.log(f"Error stably updating note '{title}': {e}", "Infra")
        return False


# --- Team & Registry ---
def get_team_registry(project_dir: str = ".") -> Dict[str, Any]:
    """Load the team registry from .jbot/agents.json."""
    agents_path = os.path.join(project_dir, ".jbot/agents.json")
    return core.load_json(agents_path, default={})


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


def send_message(
    project_dir: str, agent_name: str, body: str, subject: str = "No Subject"
) -> bool:
    """Sends a message by writing it to the .jbot/outbox directory."""
    outbox_dir = os.path.join(project_dir, ".jbot", "outbox")
    os.makedirs(outbox_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    microsecond = datetime.now().strftime("%f")
    filename = f"{timestamp}_{microsecond}_{agent_name}.txt"
    file_path = os.path.join(outbox_dir, filename)

    message_content = f"To: all\nFrom: {agent_name}\nSubject: {subject}\n\n{body}\n"
    return core.write_file(file_path, message_content)


def get_note_content(query: str) -> Optional[str]:
    """Retrieves the full content of the first nb note matching the query."""

    try:
        client = NbClient()
        note_id = None

        if query.startswith("type:") or query.startswith("#"):
            tag = query.replace("type:", "").replace("#", "")
            # Use ls for tag queries as it is more precise than q
            notes = client.ls(tags=[tag])
            if notes:
                # Sort by ID descending to get the newest by default
                notes.sort(key=lambda x: int(x.id), reverse=True)
                # Prefer notes with "Authoritative" or "Board" in title for tasks
                if tag == "tasks":
                    for n in notes:
                        if (
                            "authoritative" in n.title.lower()
                            or "board" in n.title.lower()
                        ):
                            note_id = n.id
                            core.log(f"Found task board: {n.title} ({n.id})", "Infra")
                            break
                if not note_id:
                    note_id = notes[0].id

        if not note_id:
            # 1. Search for the ID using 'nb jbot:q' which is the most reliable search for text
            notes = client.query(query)
            if notes:
                note_id = notes[0].id

        # 2. Fallback to title search if search failed
        if not note_id and query == "type:prompt":
            notes = client.query("Authoritative System Prompt")
            if notes:
                note_id = notes[0].id

        # 3. Get the actual content using the ID
        if note_id:
            return client.show(note_id)

        return None
    except Exception as e:
        core.log(f"Error fetching note '{query}' from nb: {e}", "Infra")
        return None


# --- Memory & Logs ---
def get_recent_logs(count: int = 10) -> List[Dict[str, Any]]:
    """Retrieve recent entries from the nb knowledge base."""
    try:
        # Get list of memory notes
        client = NbClient()
        notes = client.ls(tags=["memory"], limit=count)

        entries = []
        for note in notes:
            # Regex to extract agent and summary from title
            match = re.search(r"Memory: \[(.*?)\] - (.*)", note.title)
            if match:
                agent = match.group(1)
                summary = match.group(2)
                entries.append({"agent": agent, "content": {"summary": summary}})
        return entries
    except Exception as e:
        core.log(f"Error fetching logs from nb: {e}", "Infra")
        return []


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


# --- Dashboard ---
def get_recent_adrs(count: int = 5) -> List[Dict[str, str]]:
    """Retrieve the most recent ADRs from the nb knowledge base."""
    try:
        client = NbClient()
        # ADRs must have #type:adr tag
        notes = client.ls(tags=["type:adr"])
        # Sort by ID descending to get the newest by default
        notes.sort(key=lambda x: int(x.id), reverse=True)

        results = []
        for note in notes:
            # Since we filtered by tag type:adr in client.ls, we can trust these are ADRs/Architectural notes
            results.append({"id": note.id, "title": note.title})

            if len(results) >= count:
                break
        return results
    except Exception as e:
        core.log(f"Error fetching ADRs from nb: {e}", "Infra")
        return []


def generate_dashboard(output_file: str = "INDEX.md", project_dir: str = ".") -> bool:
    """Generates a markdown dashboard summarizing the project status.

    Context: [[nb:jbot:adr-193]], [[nb:jbot:adr-200]]
    """
    import jbot_tasks as tasks
    import glob

    dashboard_content = "# JBot Dashboard\n\n"
    dashboard_content += (
        f"*Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
    )

    tasks_data = tasks.parse_tasks()
    changelog_path = core.find_file_upwards("CHANGELOG.md", project_dir)

    dashboard_content += "## 🎯 Strategic Vision\n"
    if tasks_data.get("vision"):
        dashboard_content += f"> {tasks_data['vision']}\n\n"
    else:
        goal_path = core.find_file_upwards(".project_goal", project_dir)
        if goal_path and os.path.exists(goal_path):
            dashboard_content += f"> {core.read_file(goal_path)}\n\n"
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
    # Filter for truly active tasks (not marked [x]) as per ADR-193
    active_tasks = [t for t in tasks_data["active"] if "- [ ]" in t]
    if active_tasks:
        for task in active_tasks[:10]:
            # Extract agent name from task if present: - [ ] **Text** (Agent: Name)
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

    # Add Recently Completed section from Task Board
    completed_tasks = []
    for line in tasks_data["sections"]["completed"]:
        stripped = line.strip()
        if stripped.startswith("-"):
            completed_tasks.append(stripped)

    if completed_tasks:
        dashboard_content += "## ✅ Recently Completed\n"
        # Show first 5 completed tasks (most recent)
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
    else:
        dashboard_content += "No diagrams found.\n\n"

    dashboard_content += "## 📈 Status & Progress\n"
    milestone_count = 0
    if changelog_path and os.path.exists(changelog_path):
        with open(changelog_path, "r") as f:
            milestone_count = sum(1 for line in f if line.strip().startswith("- **"))

    dashboard_content += f"- **Tasks Completed:** {tasks_data['done_count']}\n"
    dashboard_content += f"- **Milestones Achieved:** {milestone_count}\n\n"

    # Technical ROI Metrics (Context: [[nb:jbot:adr-205]])
    try:
        client = NbClient()
        all_notes = client.ls()
        adr_notes = client.ls(tags=["type:adr"])

        kb_total = len(all_notes)
        adr_total = len(adr_notes)

        velocity = (
            tasks_data["done_count"] / milestone_count if milestone_count > 0 else 0
        )
        density = adr_total / milestone_count if milestone_count > 0 else adr_total

        # Calculate completion ratio: Done / (Active + Backlog + Done)
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
        core.log(f"Error calculating Technical ROI: {e}", "Infra")

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


# --- Maintenance ---
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
                core.log(f"Consolidated message: {msg_file}", "Maintenance")
            except Exception as e:
                core.log(f"Error consolidating message {msg_file}: {e}", "Maintenance")


def consolidate_memory(project_dir: str) -> None:
    """Aggregates agent memory queues into the nb knowledge base."""
    queues_dir = os.path.join(project_dir, ".jbot/queues")

    if not os.path.exists(queues_dir):
        return

    # Ensure NB environment variables for identity are respected
    env = os.environ.copy()
    if "NB_USER_NAME" not in env:
        env["NB_USER_NAME"] = "JBot System"
    if "NB_USER_EMAIL" not in env:
        env["NB_USER_EMAIL"] = "system@internal.jbot"

    client = NbClient(env=env)

    for q_file in os.listdir(queues_dir):
        if q_file.endswith(".json"):
            q_path = os.path.join(queues_dir, q_file)
            agent_name = q_file[:-5]
            try:
                content = core.load_json(q_path)
                summary = content.get("summary", "No summary")
                # Truncate summary for title to prevent 'File name too long'
                short_summary = (summary[:80] + "..") if len(summary) > 80 else summary
                title = f"Memory: [{agent_name}] - {short_summary}"
                tags = ["memory", f"agent:{agent_name}"]

                client.add(title=title, content=json.dumps(content), tags=tags)

                os.remove(q_path)
                core.log(f"Consolidated memory for {agent_name} into nb", "Maintenance")
            except Exception as e:
                core.log(
                    f"Error consolidating memory for {agent_name} to nb: {e}",
                    "Maintenance",
                )


def run_maintenance(project_dir: str) -> bool:
    """Performs all automated infrastructure maintenance tasks."""
    core.log("Starting infrastructure maintenance...", "Maintenance")
    try:
        initialize_infrastructure(project_dir)
        consolidate_messages(project_dir)
        consolidate_memory(project_dir)
        jbot_rotation.perform_rotations(project_dir)
        generate_dashboard(project_dir=project_dir)
        core.log("Maintenance complete.", "Maintenance")
        return True
    except Exception as e:
        core.log(f"Maintenance failed: {e}", "Maintenance")
        return False
