#!/usr/bin/env python3
import os
import json
import argparse
from datetime import datetime


def log(msg):
    print(f"[{datetime.now()}] JBot CLI: {msg}")


def find_file_upwards(filename, start_dir="."):
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


def get_status(project_dir):
    os.chdir(project_dir)
    goal_path = ".project_goal"
    tasks_path = "TASKS.md"

    print("\n--- JBot PAO Status ---")
    if os.path.exists(goal_path):
        with open(goal_path, "r") as f:
            print(f"\n🎯 Company Vision:\n> {f.read().strip()}")

    if os.path.exists(tasks_path):
        with open(tasks_path, "r") as f:
            lines = f.readlines()
            active_tasks = []
            done_count = 0
            in_active = False
            for line in lines:
                if "## Active Tasks" in line:
                    in_active = True
                    continue
                if in_active and line.startswith("##"):
                    in_active = False

                if in_active and line.strip().startswith("- [ ]"):
                    active_tasks.append(line.strip())
                if line.strip().startswith("- [x]"):
                    done_count += 1

            print(f"\n🚀 Active Tasks ({len(active_tasks)}):")
            for t in active_tasks[:5]:
                print(f"  {t}")
            if len(active_tasks) > 5:
                print(f"  ... and {len(active_tasks) - 5} more.")

            print(f"\n📈 Overall Progress: {done_count} tasks completed.")


def get_tasks(project_dir, show_all=False):
    os.chdir(project_dir)
    tasks_path = "TASKS.md"
    if not os.path.exists(tasks_path):
        print("Error: TASKS.md not found.")
        return

    print("\n--- JBot Task Board ---")
    with open(tasks_path, "r") as f:
        content = f.read()
        if not show_all:
            # Only show Active and Backlog
            parts = content.split("## Completed Tasks")
            print(parts[0].strip())
        else:
            print(content.strip())


def get_logs(project_dir, count=10):
    os.chdir(project_dir)
    log_path = ".jbot/memory.log"
    if not os.path.exists(log_path):
        print("No memory logs found.")
        return

    print(f"\n--- Recent Activity (Last {count}) ---")
    with open(log_path, "r") as f:
        lines = f.readlines()
        for line in lines[-count:]:
            try:
                data = json.loads(line)
                agent = data.get("agent", "unknown")
                summary = data.get("content", {}).get("summary", "No summary")
                print(f"[{agent}] {summary}")
            except Exception:
                print(line.strip())


def get_messages(project_dir, count=5):
    os.chdir(project_dir)
    msg_dir = ".jbot/messages"
    if not os.path.exists(msg_dir):
        print("No messages directory found.")
        return

    print(f"\n--- Recent Messages (Last {count}) ---")
    msg_files = sorted(
        [f for f in os.listdir(msg_dir) if f.endswith(".txt") and f != "human.txt"]
    )
    for mf in msg_files[-count:]:
        with open(os.path.join(msg_dir, mf), "r") as f:
            f.readline()  # Skip "To: all"
            second_line = f.readline().strip()  # From: agent
            third_line = f.readline().strip()  # Subject: ...
            print(f"[{mf}] {second_line} - {third_line}")


def add_task(project_dir, task_text, agent=None):
    os.chdir(project_dir)
    tasks_path = "TASKS.md"
    if not os.path.exists(tasks_path):
        print("Error: TASKS.md not found.")
        return

    with open(tasks_path, "r") as f:
        lines = f.readlines()

    new_lines = []
    added = False
    task_entry = f"- [ ] **{task_text}**"
    if agent:
        task_entry += f" (Agent: {agent})"
    task_entry += "\n"

    for line in lines:
        new_lines.append(line)
        if "## Active Tasks" in line and not added:
            new_lines.append(task_entry)
            added = True

    if not added:
        new_lines.append("\n## Active Tasks\n")
        new_lines.append(task_entry)

    with open(tasks_path, "w") as f:
        f.writelines(new_lines)

    print(f"Successfully added task: {task_text}")


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

    args = parser.parse_args()

    # Find project root if not specified
    project_root = find_file_upwards(".project_goal", args.dir)
    if not project_root:
        project_root = os.path.abspath(args.dir)
    else:
        project_root = os.path.dirname(project_root)

    if args.command == "status":
        get_status(project_root)
    elif args.command == "tasks":
        get_tasks(project_root, args.all)
    elif args.command == "add-task":
        add_task(project_root, args.text, args.agent)
    elif args.command == "logs":
        get_logs(project_root, args.count)
    elif args.command == "messages":
        get_messages(project_root, args.count)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
