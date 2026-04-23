import os
import re
import shutil
from datetime import datetime

import jbot_core as core


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
    # Memory and tasks are now handled by nb and don't require manual flat-file rotation.
    rotate_messages(
        os.path.join(project_dir, ".jbot/messages"),
        os.path.join(project_dir, ".jbot/messages/archive"),
    )
