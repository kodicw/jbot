#!/usr/bin/env python3
import os
import argparse
import subprocess
import jbot_utils as utils


def get_status(project_dir):
    os.chdir(project_dir)
    goal_path = ".project_goal"
    tasks_path = "TASKS.md"

    print("\n--- JBot Organization Status ---")
    if os.path.exists(goal_path):
        with open(goal_path, "r") as f:
            print(f"\n🎯 Company Vision:\n> {f.read().strip()}")

    tasks_data = utils.parse_tasks(tasks_path)
    print(f"\n🚀 Active Tasks ({len(tasks_data['active'])}):")
    for t in tasks_data["active"][:5]:
        print(f"  {t}")
    if len(tasks_data["active"]) > 5:
        print(f"  ... and {len(tasks_data['active']) - 5} more.")

    print(f"\n📈 Overall Progress: {tasks_data['done_count']} tasks completed.")


def get_tasks(project_dir, show_all=False):
    os.chdir(project_dir)
    tasks_path = "TASKS.md"
    if not os.path.exists(tasks_path):
        print("Error: TASKS.md not found.")
        return

    print("\n--- JBot Task Board ---")
    if not show_all:
        tasks_data = utils.parse_tasks(tasks_path)
        print("## Strategic Vision")
        print(tasks_data["vision"])
        print("\n## Active Tasks")
        for t in tasks_data["active"]:
            print(t)
        print("\n## Backlog")
        for t in tasks_data["backlog"]:
            print(t)
    else:
        with open(tasks_path, "r") as f:
            print(f.read().strip())


def get_logs(project_dir, count=10):
    os.chdir(project_dir)
    log_path = ".jbot/memory.log"
    logs = utils.get_recent_logs(log_path, count)

    if not logs:
        print("No memory logs found.")
        return

    print(f"\n--- Recent Activity (Last {len(logs)}) ---")
    for data in reversed(
        logs
    ):  # utils.get_recent_logs returns in reverse order (newest first)
        agent = data.get("agent", "unknown")
        summary = data.get("content", {}).get("summary", "No summary")
        print(f"[{agent}] {summary}")


def get_messages(project_dir, count=5):
    os.chdir(project_dir)
    msg_dir = ".jbot/messages"
    messages = utils.get_recent_messages(msg_dir, count)

    if not messages:
        print("No messages directory found.")
        return

    print(f"\n--- Recent Messages (Last {len(messages)}) ---")
    for m in messages:
        content = m["content"].split("\n")
        from_line = next(
            (line for line in content if line.startswith("From:")), "From: unknown"
        )
        subject_line = next(
            (line for line in content if line.startswith("Subject:")), "Subject: none"
        )
        print(f"[{m['filename']}] {from_line} - {subject_line}")


def handle_version(project_root, action, part=None):
    os.chdir(project_root)
    if action == "show":
        v = utils.get_version(project_root)
        print(f"Current JBot Version: v{v}")
    elif action == "bump":
        new_v = utils.bump_version(project_root, part)
        if new_v:
            print(f"Successfully bumped version to: v{new_v}")
        else:
            print("Error: Failed to bump version.")
    elif action == "tag":
        v = utils.get_version(project_root)
        tag_name = f"v{v}"
        print(f"Creating git tag: {tag_name}")
        try:
            subprocess.run(
                ["git", "tag", "-a", tag_name, "-m", f"Release {tag_name}"], check=True
            )
            print(f"Successfully created tag: {tag_name}")
        except subprocess.CalledProcessError as e:
            print(f"Error: Git tag failed - {e}")
    elif action == "release":
        if not part:
            print("Error: Must specify version part (major, minor, patch) for release.")
            return

        # Check for cleanliness
        if not utils.is_git_clean(project_root):
            print(
                "Error: Git workspace is not clean. Please commit or stash changes before release."
            )
            return

        print(f"Starting release process (bump {part})...")
        new_v = utils.bump_version(project_root, part)
        if not new_v:
            print("Error: Failed to bump version.")
            return

        # Update changelog
        if not utils.update_changelog(project_root, new_v):
            print("Warning: Failed to update CHANGELOG.md automatically.")

        tag_name = f"v{new_v}"
        try:
            # Add and commit the version bump and changelog
            subprocess.run(["git", "add", "VERSION", "CHANGELOG.md"], check=True)
            subprocess.run(
                ["git", "commit", "--no-verify", "-m", f"chore: release {tag_name}"], check=True
            )
            # Create the tag
            subprocess.run(
                ["git", "tag", "-a", tag_name, "-m", f"Release {tag_name}"], check=True
            )
            print(f"🚀 Successfully released {tag_name}")
        except subprocess.CalledProcessError as e:
            print(f"Error: Release failed during git operations - {e}")


def main():
    parser = argparse.ArgumentParser(description="JBot Centralized CLI Tool")
    parser.add_argument(
        "-d", "--dir", default=".", help="Project directory (default: .)"
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    subparsers.add_parser("status", help="Show current vision and high-level status")

    # --- Task Commands ---
    task_parser = subparsers.add_parser("task", help="Manage tasks on the board")
    task_subparsers = task_parser.add_subparsers(
        dest="task_action", help="Task actions"
    )

    # task list
    list_parser = task_subparsers.add_parser(
        "list", help="List active and backlog tasks"
    )
    list_parser.add_argument(
        "-a", "--all", action="store_true", help="Show all tasks including completed"
    )

    # task add
    add_parser = task_subparsers.add_parser("add", help="Add a new task")
    add_parser.add_argument("text", help="Task description")
    add_parser.add_argument("-a", "--agent", help="Assign to specific agent")
    add_parser.add_argument(
        "-b", "--backlog", action="store_true", help="Add to backlog instead of active"
    )

    # task update
    update_parser = task_subparsers.add_parser("update", help="Update an existing task")
    update_parser.add_argument("search", help="Search string to identify the task")
    update_parser.add_argument("-t", "--text", help="New task description")
    update_parser.add_argument("-a", "--agent", help="Reassign to agent")
    update_parser.add_argument(
        "-m", "--move", choices=["active", "backlog"], help="Move task to section"
    )

    # task done
    done_parser = task_subparsers.add_parser("done", help="Mark a task as completed")
    done_parser.add_argument("search", help="Search string to identify the task")

    # Keep old commands for compatibility
    old_tasks_parser = subparsers.add_parser("tasks", help="Alias for 'task list'")
    old_tasks_parser.add_argument(
        "-a", "--all", action="store_true", help="Show all tasks"
    )

    old_add_task_parser = subparsers.add_parser("add-task", help="Alias for 'task add'")
    old_add_task_parser.add_argument("text", help="Task description")
    old_add_task_parser.add_argument("-a", "--agent", help="Assign to specific agent")

    log_parser = subparsers.add_parser("logs", help="Show recent agent activity logs")
    log_parser.add_argument(
        "-n", "--count", type=int, default=10, help="Number of entries to show"
    )

    msg_parser = subparsers.add_parser("messages", help="Show recent agent messages")
    msg_parser.add_argument(
        "-n", "--count", type=int, default=5, help="Number of messages to show"
    )

    # --- Message Send Command ---
    send_msg_parser = subparsers.add_parser(
        "send-message", help="Send a message to all agents"
    )
    send_msg_parser.add_argument(
        "-f", "--from-agent", required=True, help="Agent sending the message"
    )
    send_msg_parser.add_argument(
        "-s", "--subject", default="No Subject", help="Message subject"
    )
    send_msg_parser.add_argument("-m", "--message", required=True, help="Message body")

    # --- Infrastructure Commands ---
    subparsers.add_parser(
        "maintenance", help="Run automated infrastructure maintenance"
    )

    subparsers.add_parser("purge", help="Archive expired directives")

    rotate_parser = subparsers.add_parser("rotate", help="Rotate infrastructure data")
    rotate_subparsers = rotate_parser.add_subparsers(
        dest="rotate_target", help="Rotate target"
    )

    memory_rotate = rotate_subparsers.add_parser("memory", help="Rotate memory logs")
    memory_rotate.add_argument(
        "-l", "--limit", type=int, default=100, help="Max entries to keep"
    )

    tasks_rotate = rotate_subparsers.add_parser("tasks", help="Rotate task board")
    tasks_rotate.add_argument(
        "-l", "--limit", type=int, default=10, help="Max completed tasks to keep"
    )

    msg_rotate = rotate_subparsers.add_parser("messages", help="Rotate agent messages")
    msg_rotate.add_argument(
        "-l", "--limit", type=int, default=50, help="Max messages to keep"
    )

    subparsers.add_parser("dashboard", help="Manually regenerate the JBot dashboard")

    version_parser = subparsers.add_parser(
        "version", help="Manage JBot versioning and releases"
    )
    version_subparsers = version_parser.add_subparsers(dest="action", help="Actions")
    version_subparsers.add_parser("show", help="Show the current version")

    bump_parser = version_subparsers.add_parser(
        "bump", help="Bump the version (major, minor, patch)"
    )
    bump_parser.add_argument(
        "part", choices=["major", "minor", "patch"], help="Version part to bump"
    )

    version_subparsers.add_parser(
        "tag", help="Create a git tag for the current version"
    )

    release_parser = version_subparsers.add_parser(
        "release", help="Automated release (bump, commit, and tag)"
    )
    release_parser.add_argument(
        "part", choices=["major", "minor", "patch"], help="Version part to bump"
    )

    args = parser.parse_args()

    # Find project root if not specified
    project_root = utils.get_project_root(args.dir)
    tasks_md_path = os.path.join(project_root, "TASKS.md")

    if args.command == "status":
        get_status(project_root)
    elif args.command == "task":
        if args.task_action == "list":
            get_tasks(project_root, args.all)
        elif args.task_action == "add":
            if utils.add_task(tasks_md_path, args.text, args.agent, args.backlog):
                print(f"Successfully added task: {args.text}")
        elif args.task_action == "update":
            if utils.update_task(
                tasks_md_path, args.search, args.text, args.agent, args.move
            ):
                print(f"Successfully updated task matching: {args.search}")
        elif args.task_action == "done":
            if utils.complete_task(tasks_md_path, args.search):
                print(f"Successfully completed task matching: {args.search}")
        else:
            task_parser.print_help()
    elif args.command == "tasks":
        get_tasks(project_root, args.all)
    elif args.command == "add-task":
        if utils.add_task(tasks_md_path, args.text, args.agent):
            print(f"Successfully added task: {args.text}")
    elif args.command == "logs":
        get_logs(project_root, args.count)
    elif args.command == "messages":
        get_messages(project_root, args.count)
    elif args.command == "send-message":
        if utils.send_message(
            project_root, args.from_agent, args.message, args.subject
        ):
            print("Message sent successfully.")
    elif args.command == "maintenance":
        utils.run_maintenance(project_root)
    elif args.command == "purge":
        count = utils.purge_directives(
            os.path.join(project_root, ".jbot/directives"),
            os.path.join(project_root, ".jbot/directives/archive"),
        )
        print(f"Purged {count} expired directives.")
    elif args.command == "rotate":
        if args.rotate_target == "memory":
            if utils.rotate_memory(
                os.path.join(project_root, ".jbot/memory.log"),
                os.path.join(project_root, ".jbot/memory.log.archive"),
                args.limit,
            ):
                print("Memory log rotated.")
            else:
                print("Memory log rotation not needed or failed.")
        elif args.rotate_target == "tasks":
            if utils.rotate_tasks(
                os.path.join(project_root, "TASKS.md"),
                os.path.join(project_root, "TASKS.archive.md"),
                args.limit,
            ):
                print("Tasks rotated.")
            else:
                print("Task rotation not needed or failed.")
        elif args.rotate_target == "messages":
            if utils.rotate_messages(
                os.path.join(project_root, ".jbot/messages"),
                os.path.join(project_root, ".jbot/messages/archive"),
                args.limit,
            ):
                print("Messages rotated.")
            else:
                print("Message rotation not needed or failed.")
        else:
            rotate_parser.print_help()
    elif args.command == "dashboard":
        if utils.generate_dashboard(project_dir=project_root):
            print("Dashboard regenerated.")
    elif args.command == "version":
        handle_version(project_root, args.action, getattr(args, "part", None))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
