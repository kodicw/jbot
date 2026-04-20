import os
import argparse
from datetime import datetime
import jbot_utils as utils


def generate_dashboard(output_file="INDEX.md", project_dir="."):
    os.chdir(project_dir)
    dashboard_content = "# JBot PAO Dashboard\n\n"
    dashboard_content += (
        f"*Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
    )

    # Find core files upwards
    goal_path = utils.find_file_upwards(".project_goal", project_dir)
    tasks_path = utils.find_file_upwards("TASKS.md", project_dir)
    changelog_path = utils.find_file_upwards("CHANGELOG.md", project_dir)

    # 1. Company Vision
    dashboard_content += "## 🎯 Company Vision\n"
    if goal_path and os.path.exists(goal_path):
        with open(goal_path, "r") as f:
            dashboard_content += f"> {f.read().strip()}\n\n"
    else:
        dashboard_content += "No current vision defined.\n\n"

    # 2. Team Roster
    dashboard_content += "## 👥 Team Roster\n"
    agents = utils.get_team_registry(project_dir)
    if agents:
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
    tasks_data = (
        utils.parse_tasks(tasks_path) if tasks_path else {"active": [], "done_count": 0}
    )
    if tasks_data["active"]:
        for task in tasks_data["active"][:10]:
            dashboard_content += f"{task}\n"
        dashboard_content += "\n"
    else:
        dashboard_content += "No active tasks.\n\n"

    # 4. Status & Progress
    dashboard_content += "## 📈 Status & Progress\n"

    # Milestone count from changelog
    milestone_count = 0
    if changelog_path and os.path.exists(changelog_path):
        with open(changelog_path, "r") as f:
            for line in f:
                if line.strip().startswith("- **"):
                    milestone_count += 1

    dashboard_content += f"- **Tasks Completed:** {tasks_data['done_count']}\n"
    dashboard_content += f"- **Milestones Achieved:** {milestone_count}\n\n"

    # 5. Recent Milestones
    dashboard_content += "## 🏆 Recent Milestones\n"
    if changelog_path and os.path.exists(changelog_path):
        with open(changelog_path, "r") as f:
            lines = f.readlines()
            milestones = [
                line.strip() for line in lines if line.strip().startswith("- **")
            ]
            for m in milestones[:5]:
                dashboard_content += f"{m}\n"
            dashboard_content += "\n"
    else:
        dashboard_content += "No changelog found.\n\n"

    with open(output_file, "w") as f:
        f.write(dashboard_content)

    utils.log(f"Dashboard generated successfully: {output_file}", "Dashboard")


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
