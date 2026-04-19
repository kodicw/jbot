import os
import argparse
import json
from datetime import datetime

def log(msg):
    print(f"[{datetime.now()}] JBot Subproject Init: {msg}")

def init_subproject(name, parent_dir=".", goal="A sub-project of JBot."):
    sub_dir = os.path.join(parent_dir, name)
    if os.path.exists(sub_dir):
        log(f"Error: Directory {sub_dir} already exists.")
        return False

    os.makedirs(sub_dir)
    os.makedirs(os.path.join(sub_dir, ".jbot", "directives"), exist_ok=True)
    os.makedirs(os.path.join(sub_dir, ".jbot", "messages"), exist_ok=True)
    os.makedirs(os.path.join(sub_dir, ".jbot", "queues"), exist_ok=True)
    os.makedirs(os.path.join(sub_dir, ".jbot", "memory"), exist_ok=True)
    
    # Initialize TASKS.md
    with open(os.path.join(sub_dir, "TASKS.md"), "w") as f:
        f.write(f"# {name} Task Board\n\n")
        f.write("## Strategic Vision\n")
        f.write(f"{goal}\n\n")
        f.write("## Active Tasks\n")
        f.write("- [ ] Initialize sub-project structure (Agent: lead) - Status: Done\n\n")
        f.write("## Backlog\n")
        f.write("- [ ] Define roadmap for {name}\n")
    
    # Initialize .project_goal
    with open(os.path.join(sub_dir, ".project_goal"), "w") as f:
        f.write(goal + "\n")
        
    # Initialize BILLING.md
    with open(os.path.join(sub_dir, "BILLING.md"), "w") as f:
        f.write(f"# {name} Billing & Token Usage\n\n")
        f.write("## Summary\n")
        f.write("- **Total Estimated Cost:** $0.0000\n")
        f.write("- **Total Tokens:** 0\n")
        f.write(f"- **Last Updated:** {datetime.now().strftime('%Y-%m-%d')}\n\n")
        f.write("## Usage Log\n")
        f.write("| Date | Agent | Tokens (In/Out) | Estimated Cost | Task |\n")
        f.write("|------|-------|-----------------|----------------|------|\n")
        f.write(f"| {datetime.now().strftime('%Y-%m-%d')} | lead | N/A | $0.00 | Initialized sub-project |\n")

    # README for directives
    with open(os.path.join(sub_dir, ".jbot", "directives", "README.md"), "w") as f:
        f.write("# Sub-Project Directives\n\n")
        f.write("This directory contains formal directives specific to this sub-project.\n")

    log(f"Successfully initialized sub-project '{name}' at {sub_dir}")
    log(f"Next step: Add a new agent to your Home Manager config pointing to {os.path.abspath(sub_dir)}")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize a JBot Sub-Project structure.")
    parser.add_argument("name", help="Name of the sub-project directory.")
    parser.add_argument("-d", "--dir", default=".", help="Parent directory (default: current directory).")
    parser.add_argument("-g", "--goal", default="A sub-project of JBot.", help="Strategic goal for the sub-project.")
    args = parser.parse_args()
    
    init_subproject(args.name, parent_dir=args.dir, goal=args.goal)
