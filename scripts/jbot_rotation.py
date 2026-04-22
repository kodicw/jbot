import os
import re
import shutil
from datetime import datetime

import jbot_core as core
import jbot_tasks as tasks


def purge_directives(dir_path: str, archive_path: str) -> int:
    """Archives expired directives from dir_path to archive_path."""
    if not os.path.exists(dir_path):
        core.log(f"Error: Directive directory {dir_path} not found.", "Purge")
        return 0

    os.makedirs(archive_path, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    purged_count = 0

    dir_files = [
        f
        for f in os.listdir(dir_path)
        if f.endswith((".txt", ".md")) and f != "README.md"
    ]

    for df in dir_files:
        is_expired = False
        df_path = os.path.join(dir_path, df)
        if os.path.isdir(df_path):
            continue

        date_match = re.search(r"(\d{4}-\d{2}-\d{2})", df)
        exp_date_from_filename = date_match.group(1) if date_match else None

        try:
            directive_content = core.read_file(df_path)
            if not directive_content:
                continue

            content_exp_match = re.search(
                r"Expiration:\s*(\d{4}-\d{2}-\d{2})", directive_content, re.IGNORECASE
            )
            if content_exp_match:
                exp_date = content_exp_match.group(1)
                if today > exp_date:
                    is_expired = True
                    core.log(f"Directive {df} expired (content: {exp_date}).", "Purge")
            elif exp_date_from_filename:
                if today > exp_date_from_filename:
                    is_expired = True
                    core.log(
                        f"Directive {df} expired (filename: {exp_date_from_filename}).",
                        "Purge",
                    )

            if is_expired:
                dest_path = os.path.join(archive_path, df)
                if os.path.exists(dest_path):
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    name, ext = os.path.splitext(df)
                    dest_path = os.path.join(archive_path, f"{name}_{timestamp}{ext}")
                shutil.move(df_path, dest_path)
                core.log(f"Archived expired directive: {df}", "Purge")
                purged_count += 1
        except Exception as e:
            core.log(f"Error processing directive {df}: {e}", "Purge")
    return purged_count


def rotate_memory(memory_log: str, archive_log: str, limit: int = 100) -> bool:
    """Rotates the memory log, moving older entries to archive."""
    if not os.path.exists(memory_log):
        return False
    try:
        with open(memory_log, "r") as f:
            lines = f.readlines()
        if len(lines) <= limit:
            return False
        to_keep = lines[-limit:]
        to_archive = lines[:-limit]
        core.log(f"Rotating memory: Archiving {len(to_archive)} entries.", "Rotate")
        with open(archive_log, "a") as f:
            f.writelines(to_archive)
        with open(memory_log, "w") as f:
            f.writelines(to_keep)
        return True
    except Exception as e:
        core.log(f"Error rotating memory log: {e}", "Rotate")
        return False


def rotate_tasks(
    tasks_file: str = "TASKS.md",
    archive_file: str = "TASKS.archive.md",
    limit: int = 20,
) -> bool:
    """Rotates the task board, moving completed tasks to archive."""
    if not os.path.exists(tasks_file):
        return False
    try:
        tasks_data = tasks.parse_tasks(tasks_file)
        sections = tasks_data["sections"]
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
            elif line.strip() and line.strip() != "...":
                new_active.append(line)
        for line in sections["backlog"][1:]:
            if "[x]" in line:
                newly_completed.append(line)
            elif line.strip() and line.strip() != "...":
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
            core.log(f"Archiving {len(to_archive)} completed tasks.", "Rotate")

        if to_archive:
            if not os.path.exists(archive_file) or os.path.getsize(archive_file) == 0:
                core.write_file(archive_file, "# JBot Task Archive\n\n")
            with open(archive_file, "a") as f:
                f.write(
                    f"## Archived on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                )
                f.writelines(to_archive)
                f.write("\n")

        with open(tasks_file, "w") as f:
            f.writelines(
                sections["header"] if sections["header"] else ["# JBot Task Board\n\n"]
            )
            f.writelines(sections["vision"])
            f.write("\n")
            f.writelines(new_active)
            if not new_active[-1].endswith("\n"):
                f.write("\n")
            f.write("\n")
            f.writelines(new_backlog)
            if not new_backlog[-1].endswith("\n"):
                f.write("\n")
            f.write("\n")
            f.writelines(sections["completed"][:1])
            f.writelines(to_keep)
        return True
    except Exception as e:
        core.log(f"Error rotating tasks: {e}", "Rotate")
        return False


def rotate_messages(msg_dir: str, archive_dir: str, limit: int = 50) -> bool:
    """Archives older messages from msg_dir to archive_dir."""
    if not os.path.exists(msg_dir):
        return False
    os.makedirs(archive_dir, exist_ok=True)
    msg_files = sorted(
        [
            f
            for f in os.listdir(msg_dir)
            if os.path.isfile(os.path.join(msg_dir, f)) and f != "human.txt"
        ]
    )
    if len(msg_files) <= limit:
        return False
    to_archive = msg_files[:-limit]
    core.log(f"Archiving {len(to_archive)} messages.", "Rotate")
    for mf in to_archive:
        shutil.move(os.path.join(msg_dir, mf), os.path.join(archive_dir, mf))
    return True


def perform_rotations(project_dir: str) -> None:
    """Executes all automated data purging and rotation tasks."""
    purge_directives(
        os.path.join(project_dir, ".jbot/directives"),
        os.path.join(project_dir, ".jbot/directives/archive"),
    )
    # Memory is now handled by nb and doesn't require manual flat-file rotation.
    rotate_tasks(
        os.path.join(project_dir, "TASKS.md"),
        os.path.join(project_dir, "TASKS.archive.md"),
    )
    rotate_messages(
        os.path.join(project_dir, ".jbot/messages"),
        os.path.join(project_dir, ".jbot/messages/archive"),
    )
