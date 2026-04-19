import os
import json
import re
import argparse
from datetime import datetime

def generate_dashboard(output_file="INDEX.md", project_dir="."):
    os.chdir(project_dir)
    dashboard_content = "# JBot PAO Dashboard\n\n"
    dashboard_content += f"*Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"

    # 1. Company Vision
    dashboard_content += "## 🎯 Company Vision\n"
    goal_path = ".project_goal"
    if os.path.exists(goal_path):
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
                dashboard_content += f"| {name} | {info.get('role')} | {info.get('description')} |\n"
            dashboard_content += "\n"
    else:
        dashboard_content += "No team registry found.\n\n"

    # 3. Active Tasks
    dashboard_content += "## 🚀 Active Tasks\n"
    tasks_path = "TASKS.md"
    if os.path.exists(tasks_path):
        with open(tasks_path, "r") as f:
            lines = f.readlines()
            active_tasks = []
            in_active_section = False
            for line in lines:
                if "## Active Tasks" in line:
                    in_active_section = True
                    continue
                if in_active_section and line.startswith("##"):
                    break
                if in_active_section and line.strip().startswith("- [ ]"):
                    active_tasks.append(line.strip())
                elif in_active_section and "In Progress" in line:
                    active_tasks.append(line.strip())
            
            if active_tasks:
                for task in active_tasks[:10]:
                    dashboard_content += f"{task}\n"
                dashboard_content += "\n"
            else:
                dashboard_content += "No active tasks.\n\n"

    # 4. Resource Health & ROI
    dashboard_content += "## 💰 Resource Health & ROI\n"
    if os.path.exists("BILLING.md"):
        with open("BILLING.md", "r") as f:
            lines = f.readlines()
            total_tokens = 0
            total_cost = 0.0
            log_entries = []
            log_header = False
            for line in lines:
                if "|" in line and "Tokens" not in line and "---" not in line:
                    parts = [p.strip() for p in line.split("|") if p.strip()]
                    if len(parts) >= 4:
                        try:
                            tokens = parts[2].split("/")
                            if len(tokens) == 2:
                                total_tokens += int(tokens[0]) + int(tokens[1])
                            cost = float(parts[3].replace("$", ""))
                            total_cost += cost
                            log_entries.append(line.strip())
                        except:
                            pass

            # Count completed tasks
            done_tasks = 0
            if os.path.exists("TASKS.md"):
                with open("TASKS.md", "r") as tf:
                    done_tasks = len([l for l in tf.readlines() if l.strip().startswith("- [x]")])

            roi = total_cost / done_tasks if done_tasks > 0 else 0.0

            dashboard_content += f"- **Total Tokens:** {total_tokens:,}\n"
            dashboard_content += f"- **Total Cost:** ${total_cost:.4f}\n"
            dashboard_content += f"- **Tasks Completed:** {done_tasks}\n"
            dashboard_content += f"- **Avg Cost/Task:** ${roi:.4f}\n\n"

            dashboard_content += "| Recent Activity | Agent | Tokens | Cost |\n"
            dashboard_content += "|-----------------|-------|--------|------|\n"
            for entry in log_entries[-5:]:
                parts = [p.strip() for p in entry.split("|") if p.strip()]
                if len(parts) >= 5:
                    dashboard_content += f"| {parts[4]} | {parts[1]} | {parts[2]} | {parts[3]} |\n"
            dashboard_content += "\n"


    # 5. Recent Milestones
    dashboard_content += "## 🏆 Recent Milestones\n"
    changelog_path = "CHANGELOG.md"
    if os.path.exists(changelog_path):
        with open(changelog_path, "r") as f:
            lines = f.readlines()
            milestones = []
            for line in lines:
                if line.startswith("- **"):
                    milestones.append(line.strip())
            
            for m in milestones[:5]:
                dashboard_content += f"{m}\n"
            dashboard_content += "\n"

    with open(output_file, "w") as f:
        f.write(dashboard_content)
    print(f"Dashboard generated successfully: {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="JBot PAO Dashboard Generator")
    parser.add_argument("-o", "--output", default="INDEX.md", help="Output file (default: INDEX.md)")
    parser.add_argument("-d", "--dir", default=".", help="Project directory (default: .)")
    args = parser.parse_args()
    
    generate_dashboard(output_file=args.output, project_dir=args.dir)
