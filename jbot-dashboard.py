import os
import json
import re
from datetime import datetime

def generate_dashboard():
    dashboard_content = "# JBot PAO Dashboard\n\n"
    dashboard_content += f"*Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"

    # 1. Company Vision
    dashboard_content += "## 🎯 Company Vision\n"
    if os.path.exists(".project_goal"):
        with open(".project_goal", "r") as f:
            dashboard_content += f"> {f.read().strip()}\n\n"
    else:
        dashboard_content += "No current vision defined.\n\n"

    # 2. Team Roster
    dashboard_content += "## 👥 Team Roster\n"
    if os.path.exists(".jbot/agents.json"):
        with open(".jbot/agents.json", "r") as f:
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
    if os.path.exists("TASKS.md"):
        with open("TASKS.md", "r") as f:
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

    # 4. Resource Health
    dashboard_content += "## 💰 Resource Health (Billing)\n"
    if os.path.exists("BILLING.md"):
        with open("BILLING.md", "r") as f:
            lines = f.readlines()
            summary = []
            log_header = False
            log_entries = []
            for line in lines:
                if line.startswith("- **Total"):
                    summary.append(line.strip())
                if line.startswith("| Date |"):
                    log_header = True
                    continue
                if log_header and line.startswith("|"):
                    log_entries.append(line.strip())
            
            for s in summary:
                dashboard_content += f"{s}\n"
            
            dashboard_content += "\n| Recent Activity | Agent | Tokens | Cost |\n"
            dashboard_content += "|-----------------|-------|--------|------|\n"
            for entry in log_entries[-5:]:
                parts = [p.strip() for p in entry.split("|") if p.strip()]
                if len(parts) >= 5:
                    dashboard_content += f"| {parts[4]} | {parts[1]} | {parts[2]} | {parts[3]} |\n"
            dashboard_content += "\n"

    # 5. Recent Milestones
    dashboard_content += "## 🏆 Recent Milestones\n"
    if os.path.exists("CHANGELOG.md"):
        with open("CHANGELOG.md", "r") as f:
            lines = f.readlines()
            milestones = []
            for line in lines:
                if line.startswith("- **"):
                    milestones.append(line.strip())
            
            for m in milestones[:5]:
                dashboard_content += f"{m}\n"
            dashboard_content += "\n"

    with open("INDEX.md", "w") as f:
        f.write(dashboard_content)
    print("Dashboard generated successfully: INDEX.md")

if __name__ == "__main__":
    generate_dashboard()
