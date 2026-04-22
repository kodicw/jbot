import os
import json
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
import jbot_core as core
import jbot_tasks as tasks
import jbot_rotation


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
    import subprocess

    try:
        # Use 'nb jbot q --tags <query>' to find the note reliably
        # Then use 'nb jbot show' to get the content
        tag = query.replace("type:", "").replace("input:", "")
        
        # 1. Find the note ID
        search_res = subprocess.run(
            ["nb", "jbot", "q", "--tags", tag, "--limit", "1"],
            capture_output=True, text=True, env={**os.environ, "EDITOR": "cat"}
        )
        if search_res.returncode != 0 or not search_res.stdout.strip():
            return None
            
        # Extract ID (e.g. [jbot:47] -> 47)
        import re
        match = re.search(r"\[jbot:(\d+)\]", search_res.stdout)
        if not match:
            return None
        note_id = match.group(1)

        # 2. Show the content
        result = subprocess.run(
            ["nb", "jbot", "show", note_id, "--print"],
            capture_output=True,
            text=True,
            env={**os.environ, "EDITOR": "cat"},
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        return None
    except Exception as e:
        core.log(f"Error fetching note '{query}' from nb: {e}", "Infra")
        return None


# --- Memory & Logs ---
def get_recent_logs(log_path: str, count: int = 10) -> List[Dict[str, Any]]:
    """Retrieve recent entries from the nb knowledge base."""
    import subprocess

    try:
        # Get list of memory notes
        # nb jbot:ls format: [jbot:ID] Memory: [Agent] - Summary
        result = subprocess.run(
            ["nb", "jbot:ls", "--tags", "memory", "--limit", str(count)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return []

        entries = []
        lines = result.stdout.strip().split("\n")
        for line in lines:
            if not line:
                continue
            # Regex to extract agent and summary from title
            match = re.search(r"Memory: \[(.*?)\] - (.*)", line)
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
def generate_dashboard(output_file: str = "INDEX.md", project_dir: str = ".") -> bool:
    """Generates a markdown dashboard summarizing the project status."""
    dashboard_content = "# JBot Dashboard\n\n"
    dashboard_content += (
        f"*Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
    )

    goal_path = core.find_file_upwards(".project_goal", project_dir)
    tasks_path = core.find_file_upwards("TASKS.md", project_dir)
    changelog_path = core.find_file_upwards("CHANGELOG.md", project_dir)

    dashboard_content += "## 🎯 Company Vision\n"
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
    tasks_data = (
        tasks.parse_tasks(tasks_path) if tasks_path else {"active": [], "done_count": 0}
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

    import subprocess

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
                tags = f"memory,agent:{agent_name}"

                # Ensure NB environment variables for identity are respected
                env = os.environ.copy()
                if "NB_USER_NAME" not in env:
                    env["NB_USER_NAME"] = "JBot System"
                if "NB_USER_EMAIL" not in env:
                    env["NB_USER_EMAIL"] = "system@internal.jbot"

                # Execute nb add (non-interactively)
                subprocess.run(
                    [
                        "nb",
                        "jbot:add",
                        "--title",
                        title,
                        "--tags",
                        tags,
                        "--content",
                        json.dumps(content),
                    ],
                    check=True,
                    capture_output=True,
                    env=env,
                )
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
