import os
import json
import re
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

def parse_billing_file(billing_path):
    """Parses a BILLING.md file and returns stats."""
    stats = {
        "total_tokens": 0,
        "total_cost": 0.0,
        "agents": {}, # { name: { tokens: 0, cost: 0.0, tasks: set() } }
        "log_entries": []
    }
    
    if not os.path.exists(billing_path):
        return stats

    with open(billing_path, "r") as f:
        lines = f.readlines()
        for line in lines:
            if "|" in line and "Tokens" not in line and "---" not in line:
                parts = [p.strip() for p in line.split("|") if p.strip()]
                if len(parts) >= 4:
                    try:
                        agent_name = parts[1]
                        tokens_str = parts[2].split("/")
                        tokens = 0
                        if len(tokens_str) == 2:
                            tokens = int(tokens_str[0].replace(",", "")) + int(tokens_str[1].replace(",", ""))
                        cost = float(parts[3].replace("$", ""))
                        task_name = parts[4] if len(parts) >= 5 else "Unknown"

                        stats["total_tokens"] += tokens
                        stats["total_cost"] += cost
                        stats["log_entries"].append(line.strip())

                        if agent_name not in stats["agents"]:
                            stats["agents"][agent_name] = {"tokens": 0, "cost": 0.0, "tasks": set()}
                        
                        stats["agents"][agent_name]["tokens"] += tokens
                        stats["agents"][agent_name]["cost"] += cost
                        if task_name != "N/A" and "Initialized" not in task_name:
                            stats["agents"][agent_name]["tasks"].add(task_name)
                    except Exception as e:
                        # print(f"Error parsing line: {line.strip()} - {e}")
                        pass
    return stats

def generate_dashboard(output_file="INDEX.md", project_dir="."):
    os.chdir(project_dir)
    dashboard_content = "# JBot PAO Dashboard\n\n"
    dashboard_content += f"*Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"

    # Find core files upwards
    goal_path = find_file_upwards(".project_goal", project_dir)
    tasks_path = find_file_upwards("TASKS.md", project_dir)
    billing_path = find_file_upwards("BILLING.md", project_dir)
    changelog_path = find_file_upwards("CHANGELOG.md", project_dir)

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
                dashboard_content += f"| {name} | {info.get('role')} | {info.get('description')} |\n"
            dashboard_content += "\n"
    else:
        dashboard_content += "No team registry found.\n\n"

    # 3. Active Tasks
    dashboard_content += "## 🚀 Active Tasks\n"
    if tasks_path and os.path.exists(tasks_path):
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
    else:
        dashboard_content += "No Task Board found.\n\n"

    # 4. Resource Health & ROI
    dashboard_content += "## 💰 Resource Health & ROI\n"
    
    # Discovery of sub-projects
    sub_projects = []
    for item in os.listdir("."):
        if os.path.isdir(item) and not item.startswith(".") and item != "tests":
            if os.path.exists(os.path.join(item, ".jbot")):
                sub_projects.append(item)

    main_stats = parse_billing_file(billing_path) if billing_path else None
    
    total_tokens = main_stats["total_tokens"] if main_stats else 0
    total_cost = main_stats["total_cost"] if main_stats else 0.0
    
    sub_project_stats = {}
    for sp in sub_projects:
        sp_billing = os.path.join(sp, "BILLING.md")
        if os.path.exists(sp_billing):
            sp_stats = parse_billing_file(sp_billing)
            sub_project_stats[sp] = sp_stats
            total_tokens += sp_stats["total_tokens"]
            total_cost += sp_stats["total_cost"]

    # Global ROI
    done_tasks = 0
    if tasks_path and os.path.exists(tasks_path):
        with open(tasks_path, "r") as tf:
            done_tasks = len([l for l in tf.readlines() if l.strip().startswith("- [x]")])

    dashboard_content += f"- **Total Tokens (Org-wide):** {total_tokens:,}\n"
    dashboard_content += f"- **Total Cost (Org-wide):** ${total_cost:.4f}\n"
    dashboard_content += f"- **Global Avg Cost/Done Task:** ${total_cost / done_tasks if done_tasks > 0 else 0:.6f}\n\n"

    if main_stats:
        dashboard_content += "### 🤖 Agent Efficiency (Main Project)\n"
        dashboard_content += "| Agent | Tasks | Tokens | Cost | Avg Cost/Task |\n"
        dashboard_content += "|-------|-------|--------|------|---------------|\n"
        for name, info in sorted(main_stats["agents"].items(), key=lambda x: x[1]['cost'], reverse=True):
            task_count = len(info["tasks"])
            avg = info["cost"] / task_count if task_count > 0 else 0
            dashboard_content += f"| {name} | {task_count} | {info['tokens']:,} | ${info['cost']:.4f} | ${avg:.6f} |\n"
        dashboard_content += "\n"

        dashboard_content += "### 🕒 Recent Activity\n"
        dashboard_content += "| Recent Activity | Agent | Tokens | Cost |\n"
        dashboard_content += "|-----------------|-------|--------|------|\n"
        for entry in main_stats["log_entries"][-5:]:
            parts = [p.strip() for p in entry.split("|") if p.strip()]
            if len(parts) >= 5:
                dashboard_content += f"| {parts[4]} | {parts[1]} | {parts[2]} | {parts[3]} |\n"
        dashboard_content += "\n"

    # 5. Sub-Projects
    dashboard_content += "## 📂 Sub-Projects\n"
    if sub_projects:
        for sp in sub_projects:
            sp_info = sub_project_stats.get(sp)
            if sp_info:
                dashboard_content += f"- **{sp}**: {sp_info['total_tokens']:,} tokens, ${sp_info['total_cost']:.4f}\n"
            else:
                dashboard_content += f"- **{sp}**: No billing data.\n"
        dashboard_content += "\n"
    else:
        dashboard_content += "No sub-projects detected.\n\n"

    # 6. Recent Milestones
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
    
    # Update BILLING.md summary (main project only)
    if billing_path and os.path.exists(billing_path) and main_stats:
        with open(billing_path, "r") as f:
            billing_lines = f.readlines()
        
        new_billing_lines = []
        in_summary = False
        for line in billing_lines:
            if "## Summary" in line:
                in_summary = True
                new_billing_lines.append(line)
                new_billing_lines.append(f"- **Total Estimated Cost:** ${main_stats['total_cost']:.4f}\n")
                new_billing_lines.append(f"- **Total Tokens:** {main_stats['total_tokens']:,}\n")
                new_billing_lines.append(f"- **Last Updated:** {datetime.now().strftime('%Y-%m-%d')}\n")
                continue
            
            if in_summary:
                if line.startswith("- **") or line.strip() == "":
                    continue
                else:
                    in_summary = False
            
            new_billing_lines.append(line)
            
        with open(billing_path, "w") as f:
            f.writelines(new_billing_lines)
        print(f"Billing summary updated: {billing_path}")

    print(f"Dashboard generated successfully: {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="JBot PAO Dashboard Generator")
    parser.add_argument("-o", "--output", default="INDEX.md", help="Output file (default: INDEX.md)")
    parser.add_argument("-d", "--dir", default=".", help="Project directory (default: .)")
    args = parser.parse_args()
    
    generate_dashboard(output_file=args.output, project_dir=args.dir)
