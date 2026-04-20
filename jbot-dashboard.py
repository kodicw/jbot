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

def parse_tasks_file(tasks_path):
    """Parses a TASKS.md file and returns active tasks and completion count."""
    data = {
        "active": [],
        "done_count": 0
    }
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
    main_tasks = parse_tasks_file(tasks_path) if tasks_path else {"active": [], "done_count": 0}
    if main_tasks["active"]:
        for task in main_tasks["active"][:10]:
            dashboard_content += f"{task}\n"
        dashboard_content += "\n"
    else:
        dashboard_content += "No active tasks.\n\n"

    # 4. Resource Health & ROI
    dashboard_content += "## 💰 Resource Health & ROI\n"
    
    # Discovery of sub-projects
    sub_projects = []
    for item in os.listdir("."):
        if os.path.isdir(item) and not item.startswith(".") and item != "tests":
            if os.path.exists(os.path.join(item, ".jbot")):
                sub_projects.append(item)

    main_stats = parse_billing_file(billing_path) if billing_path else None
    main_milestone_count = parse_changelog_file(changelog_path) if changelog_path else 0
    
    total_tokens = main_stats["total_tokens"] if main_stats else 0
    total_cost = main_stats["total_cost"] if main_stats else 0.0
    total_milestones = main_milestone_count
    
    sub_project_stats = {}
    total_done_tasks = main_tasks["done_count"]

    for sp in sub_projects:
        sp_billing = os.path.join(sp, "BILLING.md")
        sp_tasks_path = os.path.join(sp, "TASKS.md")
        sp_changelog = os.path.join(sp, "CHANGELOG.md")
        
        sp_info = {"billing": None, "tasks": None, "milestones": 0}
        if os.path.exists(sp_billing):
            sp_info["billing"] = parse_billing_file(sp_billing)
            total_tokens += sp_info["billing"]["total_tokens"]
            total_cost += sp_info["billing"]["total_cost"]
        
        if os.path.exists(sp_tasks_path):
            sp_info["tasks"] = parse_tasks_file(sp_tasks_path)
            total_done_tasks += sp_info["tasks"]["done_count"]

        if os.path.exists(sp_changelog):
            sp_info["milestones"] = parse_changelog_file(sp_changelog)
            total_milestones += sp_info["milestones"]
            
        sub_project_stats[sp] = sp_info

    dashboard_content += f"- **Total Tokens (Org-wide):** {total_tokens:,}\n"
    dashboard_content += f"- **Total Cost (Org-wide):** ${total_cost:.4f}\n"
    dashboard_content += f"- **Global Avg Cost/Done Task:** ${total_cost / total_done_tasks if total_done_tasks > 0 else 0:.6f} ({total_done_tasks} tasks)\n"
    dashboard_content += f"- **Global Avg Cost/Milestone:** ${total_cost / total_milestones if total_milestones > 0 else 0:.6f} ({total_milestones} milestones)\n\n"

    if main_stats:
        dashboard_content += "### 🤖 Agent Efficiency (Main Project)\n"
        dashboard_content += "| Agent | Tasks | Tokens | Cost | Avg Cost/Task |\n"
        dashboard_content += "|-------|-------|--------|------|---------------|\n"
        for name, info in sorted(main_stats["agents"].items(), key=lambda x: x[1]['cost'], reverse=True):
            task_count = len(info["tasks"])
            avg = info["cost"] / task_count if task_count > 0 else 0
            dashboard_content += f"| {name} | {task_count} | {info['tokens']:,} | ${info['cost']:.4f} | ${avg:.6f} |\n"
        dashboard_content += "\n"

    # 5. Sub-Projects
    dashboard_content += "## 📂 Sub-Projects\n"
    if sub_projects:
        dashboard_content += "| Sub-Project | Status | Tasks (Active/Done) | Milestones | Cost | Tokens |\n"
        dashboard_content += "|-------------|--------|---------------------|------------|------|--------|\n"
        for sp in sub_projects:
            info = sub_project_stats.get(sp)
            billing = info.get("billing")
            tasks = info.get("tasks")
            milestones = info.get("milestones", 0)
            
            cost_str = f"${billing['total_cost']:.4f}" if billing else "$0.0000"
            tokens_str = f"{billing['total_tokens']:,}" if billing else "0"
            tasks_str = f"{len(tasks['active'])} / {tasks['done_count']}" if tasks else "N/A"
            status = "Active" if tasks and tasks["active"] else "Idle"
            
            dashboard_content += f"| {sp} | {status} | {tasks_str} | {milestones} | {cost_str} | {tokens_str} |\n"
        dashboard_content += "\n"
        
        # Detail active tasks for sub-projects
        for sp in sub_projects:
            tasks = sub_project_stats[sp].get("tasks")
            if tasks and tasks["active"]:
                dashboard_content += f"**{sp} Active Tasks:**\n"
                for t in tasks["active"][:3]:
                    dashboard_content += f"- {t}\n"
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
