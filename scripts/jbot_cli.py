#!/usr/bin/env python3
import os
import argparse
import subprocess
import jbot_core as core
import jbot_tasks as tasks
import jbot_infra as infra
import jbot_rotation
import jbot_agent


def get_status(project_dir: str) -> None:
    """Displays the high-level project vision and active tasks status."""
    os.chdir(project_dir)
    goal_path = ".project_goal"
    tasks_path = "TASKS.md"

    print("\n--- JBot Organization Status ---")
    if os.path.exists(goal_path):
        with open(goal_path, "r") as f:
            print(f"\n🎯 Company Vision:\n> {f.read().strip()}")

    tasks_data = tasks.parse_tasks(tasks_path)
    print(f"\n🚀 Active Tasks ({len(tasks_data['active'])}):")
    for t in tasks_data["active"][:5]:
        print(f"  {t}")
    if len(tasks_data["active"]) > 5:
        print(f"  ... and {len(tasks_data['active']) - 5} more.")

    print(f"\n📈 Overall Progress: {tasks_data['done_count']} tasks completed.")


def get_tasks(project_dir: str, show_all: bool = False) -> None:
    """Lists tasks from the project task board."""
    os.chdir(project_dir)
    tasks_path = "TASKS.md"
    if not os.path.exists(tasks_path):
        print("Error: TASKS.md not found.")
        return

    print("\n--- JBot Task Board ---")
    if not show_all:
        tasks_data = tasks.parse_tasks(tasks_path)
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


def get_logs(project_dir: str, count: int = 10) -> None:
    """Displays recent agent activity logs from the memory log."""
    os.chdir(project_dir)
    log_path = ".jbot/memory.log"
    logs = infra.get_recent_logs(log_path, count)

    if not logs:
        print("No memory logs found.")
        return

    print(f"\n--- Recent Activity (Last {len(logs)}) ---")
    for data in reversed(logs):
        agent = data.get("agent", "unknown")
        summary = data.get("content", {}).get("summary", "No summary")
        print(f"[{agent}] {summary}")


def get_messages(project_dir: str, count: int = 5) -> None:
    """Displays recent inter-agent messages."""
    os.chdir(project_dir)
    msg_dir = ".jbot/messages"
    messages = infra.get_recent_messages(msg_dir, count)

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


def handle_version(project_root: str, action: str, part: str = None) -> None:
    """Handles version management and automated releases."""
    os.chdir(project_root)
    if action == "show":
        v = core.get_version(project_root)
        print(f"Current JBot Version: v{v}")
    elif action == "bump":
        new_v = core.bump_version(project_root, part)
        if new_v:
            print(f"Successfully bumped version to: v{new_v}")
        else:
            print("Error: Failed to bump version.")
    elif action == "tag":
        v = core.get_version(project_root)
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

        if not core.is_git_clean(project_root):
            print(
                "Error: Git workspace is not clean. Please commit or stash changes before release."
            )
            return

        print(f"Starting release process (bump {part})...")
        new_v = core.bump_version(project_root, part)
        if not new_v:
            print("Error: Failed to bump version.")
            return

        if not core.update_changelog(project_root, new_v):
            print("Warning: Failed to update CHANGELOG.md automatically.")

        tag_name = f"v{new_v}"
        try:
            subprocess.run(["git", "add", "VERSION", "CHANGELOG.md"], check=True)
            subprocess.run(
                ["git", "commit", "--no-verify", "-m", f"chore: release {tag_name}"],
                check=True,
            )
            subprocess.run(
                ["git", "tag", "-a", tag_name, "-m", f"Release {tag_name}"], check=True
            )
            print(f"🚀 Successfully released {tag_name}")
        except subprocess.CalledProcessError as e:
            print(f"Error: Release failed during git operations - {e}")


def main():
    """JBot Centralized CLI Entry Point."""
    parser = argparse.ArgumentParser(description="JBot Centralized CLI Tool")
    parser.add_argument(
        "-d", "--dir", default=".", help="Project directory (default: .)"
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Status
    subparsers.add_parser("status", help="Show current vision and status")

    # Tasks
    task_parser = subparsers.add_parser("task", help="Manage tasks")
    task_subparsers = task_parser.add_subparsers(
        dest="task_action", help="Task actions"
    )
    list_parser = task_subparsers.add_parser("list", help="List tasks")
    list_parser.add_argument("-a", "--all", action="store_true", help="Show all")
    add_parser = task_subparsers.add_parser("add", help="Add task")
    add_parser.add_argument("text", help="Description")
    add_parser.add_argument("-a", "--agent", help="Assign agent")
    add_parser.add_argument(
        "-b", "--backlog", action="store_true", help="Add to backlog"
    )
    update_parser = task_subparsers.add_parser("update", help="Update task")
    update_parser.add_argument("search", help="Search string")
    update_parser.add_argument("-t", "--text", help="New description")
    update_parser.add_argument("-a", "--agent", help="Reassign agent")
    update_parser.add_argument(
        "-m", "--move", choices=["active", "backlog"], help="Move section"
    )
    done_parser = task_subparsers.add_parser("done", help="Mark completed")
    done_parser.add_argument("search", help="Search string")

    # Logs & Messages
    subparsers.add_parser("logs", help="Show activity logs").add_argument(
        "-n", "--count", type=int, default=10
    )
    subparsers.add_parser("messages", help="Show agent messages").add_argument(
        "-n", "--count", type=int, default=5
    )
    send_msg_parser = subparsers.add_parser("send-message", help="Send a message")
    send_msg_parser.add_argument("-f", "--from-agent", required=True)
    send_msg_parser.add_argument("-s", "--subject", default="No Subject")
    send_msg_parser.add_argument("-m", "--message", required=True)

    # Infra
    subparsers.add_parser("maintenance", help="Run maintenance")
    subparsers.add_parser("purge", help="Archive expired directives")
    rotate_parser = subparsers.add_parser("rotate", help="Rotate data")
    rotate_sub = rotate_parser.add_subparsers(dest="rotate_target")
    rotate_sub.add_parser("memory").add_argument("-l", "--limit", type=int, default=100)
    rotate_sub.add_parser("tasks").add_argument("-l", "--limit", type=int, default=10)
    rotate_sub.add_parser("messages").add_argument(
        "-l", "--limit", type=int, default=50
    )
    subparsers.add_parser("dashboard", help="Regenerate dashboard")

    # Agent
    agent_parser = subparsers.add_parser("agent", help="Run a JBot agent")
    agent_parser.add_argument("--name")
    agent_parser.add_argument("--role")
    agent_parser.add_argument("--desc")
    agent_parser.add_argument("--prompt")
    agent_parser.add_argument("--gemini")

    # Versioning
    v_parser = subparsers.add_parser("version", help="Manage versioning")
    v_sub = v_parser.add_subparsers(dest="action")
    v_sub.add_parser("show")
    v_sub.add_parser("bump").add_argument("part", choices=["major", "minor", "patch"])
    v_sub.add_parser("tag")
    v_sub.add_parser("release").add_argument(
        "part", choices=["major", "minor", "patch"]
    )

    args = parser.parse_args()
    project_root = core.get_project_root(args.dir)
    tasks_path = os.path.join(project_root, "TASKS.md")

    if args.command == "status":
        get_status(project_root)
    elif args.command == "task":
        if args.task_action == "list":
            get_tasks(project_root, args.all)
        elif args.task_action == "add":
            if tasks.add_task(tasks_path, args.text, args.agent, args.backlog):
                print(f"Added task: {args.text}")
        elif args.task_action == "update":
            if tasks.update_task(
                tasks_path, args.search, args.text, args.agent, args.move
            ):
                print(f"Updated task: {args.search}")
        elif args.task_action == "done":
            if tasks.complete_task(tasks_path, args.search):
                print(f"Completed task: {args.search}")
        else:
            task_parser.print_help()
    elif args.command == "logs":
        get_logs(project_root, args.count)
    elif args.command == "messages":
        get_messages(project_root, args.count)
    elif args.command == "send-message":
        if infra.send_message(
            project_root, args.from_agent, args.message, args.subject
        ):
            print("Message sent.")
    elif args.command == "maintenance":
        infra.run_maintenance(project_root)
    elif args.command == "purge":
        c = jbot_rotation.purge_directives(
            os.path.join(project_root, ".jbot/directives"),
            os.path.join(project_root, ".jbot/directives/archive"),
        )
        print(f"Purged {c} directives.")
    elif args.command == "rotate":
        if args.rotate_target == "memory":
            if jbot_rotation.rotate_memory(
                os.path.join(project_root, ".jbot/memory.log"),
                os.path.join(project_root, ".jbot/memory.log.archive"),
                args.limit,
            ):
                print("Memory rotated.")
        elif args.rotate_target == "tasks":
            if jbot_rotation.rotate_tasks(
                os.path.join(project_root, "TASKS.md"),
                os.path.join(project_root, "TASKS.archive.md"),
                args.limit,
            ):
                print("Tasks rotated.")
        elif args.rotate_target == "messages":
            if jbot_rotation.rotate_messages(
                os.path.join(project_root, ".jbot/messages"),
                os.path.join(project_root, ".jbot/messages/archive"),
                args.limit,
            ):
                print("Messages rotated.")
        else:
            rotate_parser.print_help()
    elif args.command == "dashboard":
        if infra.generate_dashboard(project_dir=project_root):
            print("Dashboard regenerated.")
    elif args.command == "agent":
        jbot_agent.run_agent(
            name=args.name,
            role=args.role,
            description=args.desc,
            project_dir=project_root,
            prompt_file=args.prompt,
            gemini_pkg=args.gemini,
        )
    elif args.command == "version":
        handle_version(project_root, args.action, getattr(args, "part", None))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
