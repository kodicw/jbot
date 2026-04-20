import os
import json
import argparse
from datetime import datetime


def find_file_upwards(filename, start_dir):
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


def parse_tasks_file(tasks_path):
    """Parses a TASKS.md file and returns active tasks and completion count."""
    data = {"active": [], "done_count": 0}
    if not os.path.exists(tasks_path):
        return data

    with open(tasks_path, "r") as f:
        lines = f.readlines()
        in_active_section = False
        for line in lines:
            if "## Active Tasks" in line:
                in_active_section = True
                continue
            if in_active_section and line.startswith("##"):
                in_active_section = False

            if in_active_section and line.strip().startswith("- [ ]"):
                data["active"].append(line.strip())
            elif in_active_section and "In Progress" in line:
                data["active"].append(line.strip())

            if line.strip().startswith("- [x]"):
                data["done_count"] += 1
    return data


def parse_changelog_file(changelog_path):
    """Parses a CHANGELOG.md file and returns the count of milestones."""
    count = 0
    if not os.path.exists(changelog_path):
        return count

    with open(changelog_path, "r") as f:
        lines = f.readlines()
        for line in lines:
            if line.strip().startswith("- **"):
                count += 1
    return count


def parse_billing_file(billing_path):
    """Parses a billing.json file and returns the total cost."""
    data = {"total_cost": 0.0, "currency": "USD"}
    if not os.path.exists(billing_path):
        return data

    try:
        with open(billing_path, "r") as f:
            data = json.load(f)
    except Exception:
        pass
    return data


def generate_dashboard(output_file="INDEX.md", project_dir="."):
    os.chdir(project_dir)
    dashboard_content = "# JBot PAO Dashboard\n\n"
    dashboard_content += (
        f"*Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
    )

    # Find core files upwards
    goal_path = find_file_upwards(".project_goal", project_dir)
    tasks_path = find_file_upwards("TASKS.md", project_dir)
    changelog_path = find_file_upwards("CHANGELOG.md", project_dir)
    billing_path = os.path.join(project_dir, ".jbot/billing.json")

    # 1. Company Vision
    dashboard_content += "## 🎯 Company Vision\n"
    if goal_path and os.path.exists(goal_path):
        with open(goal_path, "r") as f:
            dashboard_content += f"> {f.read().strip()}\n\n"
    else:
        dashboard_content += "No current vision defined.\n\n"

    # 2. Team Roster
    dashboard_content += "## 👥 Team Roster\n"
    agents_path = ".jbot/agents.json"
    if os.path.exists(agents_path):
        with open(agents_path, "r") as f:
            agents = json.load(f)
            dashboard_content += "| Agent | Role | Description |\n"
            dashboard_content += "|-------|------|-------------|\n"
            for name, info in agents.items():
                dashboard_content += (
                    f"| {name} | {info.get('role')} | {info.get('description')} |\n"
                )
            dashboard_content += "\n"
    else:
        dashboard_content += "No team registry found.\n\n"

    # 3. Active Tasks
    dashboard_content += "## 🚀 Active Tasks\n"
    main_tasks = (
        parse_tasks_file(tasks_path) if tasks_path else {"active": [], "done_count": 0}
    )
    if main_tasks["active"]:
        for task in main_tasks["active"][:10]:
            dashboard_content += f"{task}\n"
        dashboard_content += "\n"
    else:
        dashboard_content += "No active tasks.\n\n"

    # 4. Status & Progress
    dashboard_content += "## 📈 Status & Progress\n"
    main_milestone_count = parse_changelog_file(changelog_path) if changelog_path else 0
    billing_data = parse_billing_file(billing_path)
    total_cost = billing_data.get("total_cost", 0.0)
    currency = billing_data.get("currency", "USD")

    dashboard_content += f"- **Tasks Completed:** {main_tasks['done_count']}\n"
    dashboard_content += f"- **Milestones Achieved:** {main_milestone_count}\n"

    # ROI Metrics
    if total_cost > 0:
        avg_cost_milestone = (
            total_cost / main_milestone_count if main_milestone_count > 0 else 0
        )
        avg_cost_task = (
            total_cost / main_tasks["done_count"] if main_tasks["done_count"] > 0 else 0
        )
        dashboard_content += (
            f"- **Total Estimated Cost:** {total_cost:.2f} {currency}\n"
        )
        dashboard_content += (
            f"- **Avg Cost per Milestone (ROI):** {avg_cost_milestone:.3f} {currency}\n"
        )
        dashboard_content += (
            f"- **Avg Cost per Task:** {avg_cost_task:.3f} {currency}\n"
        )

    dashboard_content += "\n"

    # 5. Recent Milestones
    dashboard_content += "## 🏆 Recent Milestones\n"
    if changelog_path and os.path.exists(changelog_path):
        with open(changelog_path, "r") as f:
            lines = f.readlines()
            milestones = []
            for line in lines:
                if line.startswith("- **"):
                    milestones.append(line.strip())

            for m in milestones[:5]:
                dashboard_content += f"{m}\n"
            dashboard_content += "\n"
    else:
        dashboard_content += "No changelog found.\n\n"

    with open(output_file, "w") as f:
        f.write(dashboard_content)

    print(f"Dashboard generated successfully: {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="JBot PAO Dashboard Generator")
    parser.add_argument(
        "-o", "--output", default="INDEX.md", help="Output file (default: INDEX.md)"
    )
    parser.add_argument(
        "-d", "--dir", default=".", help="Project directory (default: .)"
    )
    args = parser.parse_args()

    generate_dashboard(output_file=args.output, project_dir=args.dir)
