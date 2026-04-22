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
    v_sub.add_parser("release").add_argument("part", choices=["major", "minor", "patch"])

    # Human Interaction
    subparsers.add_parser("human", help="Interact with the organization (TUI)")

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
    elif args.command == "human":
        jbot_tui.main()
    elif args.command == "version":
        handle_version(project_root, args.action, getattr(args, "part", None))
    else:
        parser.print_help()
