#!/usr/bin/env python3
import os
import argparse
import subprocess
import jbot_utils as utils


def get_status(project_dir):
    os.chdir(project_dir)
    goal_path = ".project_goal"
    tasks_path = "TASKS.md"

    print("\n--- JBot PAO Status ---")
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
            subprocess.run(["git", "tag", "-a", tag_name, "-m", f"Release {tag_name}"], check=True)
            print(f"Successfully created tag: {tag_name}")
        except subprocess.CalledProcessError as e:
            print(f"Error: Git tag failed - {e}")


def main():
    parser = argparse.ArgumentParser(description="JBot Centralized CLI Tool")
    parser.add_argument(
        "-d", "--dir", default=".", help="Project directory (default: .)"
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    subparsers.add_parser("status", help="Show current vision and high-level status")

    task_parser = subparsers.add_parser("tasks", help="List active and backlog tasks")
    task_parser.add_argument(
        "-a", "--all", action="store_true", help="Show all tasks including completed"
    )

    add_task_parser = subparsers.add_parser(
        "add-task", help="Add a new task to the board"
    )
    add_task_parser.add_argument("text", help="Task description")
    add_task_parser.add_argument("-a", "--agent", help="Assign to specific agent")

    log_parser = subparsers.add_parser("logs", help="Show recent agent activity logs")
    log_parser.add_argument(
        "-n", "--count", type=int, default=10, help="Number of entries to show"
    )

    msg_parser = subparsers.add_parser("messages", help="Show recent agent messages")
    msg_parser.add_argument(
        "-n", "--count", type=int, default=5, help="Number of messages to show"
    )

    version_parser = subparsers.add_parser("version", help="Manage JBot versioning and releases")
    version_subparsers = version_parser.add_subparsers(dest="action", help="Actions")
    version_subparsers.add_parser("show", help="Show the current version")
    bump_parser = version_subparsers.add_parser("bump", help="Bump the version (major, minor, patch)")
    bump_parser.add_argument("part", choices=["major", "minor", "patch"], help="Version part to bump")
    version_subparsers.add_parser("tag", help="Create a git tag for the current version")

    args = parser.parse_args()

    # Find project root if not specified
    project_root = utils.get_project_root(args.dir)

    if args.command == "status":
        get_status(project_root)
    elif args.command == "tasks":
        get_tasks(project_root, args.all)
    elif args.command == "add-task":
        if utils.add_task(
            os.path.join(project_root, "TASKS.md"), args.text, args.agent
        ):
            print(f"Successfully added task: {args.text}")
    elif args.command == "logs":
        get_logs(project_root, args.count)
    elif args.command == "messages":
        get_messages(project_root, args.count)
    elif args.command == "version":
        handle_version(project_root, args.action, getattr(args, "part", None))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
