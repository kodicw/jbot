#!/usr/bin/env python3
"""
JBot Sub-Project Initializer
Standardizes the creation of nested PAO (Professional Autonomous Organization) sub-projects.

Usage:
    python3 jbot-init-subproject.py <name> [options]

Options:
    -d, --dir <path>       Parent directory (default: current directory)
    -g, --goal <string>    Strategic goal for the sub-project
    -s, --supervisor <name> Name of the supervisor agent
"""

import os
import argparse
import json
from datetime import datetime

def log(msg):
    print(f"[{datetime.now()}] JBot Subproject Init: {msg}")

def init_subproject(name, parent_dir=".", goal="A sub-project of JBot.", supervisor=None):
    sub_dir = os.path.join(parent_dir, name)
    if not os.path.exists(sub_dir):
        os.makedirs(sub_dir)
        log(f"Created directory {sub_dir}")
    else:
        log(f"Directory {sub_dir} already exists. Initializing missing components...")

    # Core JBot structure
    os.makedirs(os.path.join(sub_dir, ".jbot", "directives"), exist_ok=True)
    os.makedirs(os.path.join(sub_dir, ".jbot", "messages"), exist_ok=True)
    os.makedirs(os.path.join(sub_dir, ".jbot", "queues"), exist_ok=True)
    os.makedirs(os.path.join(sub_dir, ".jbot", "memory"), exist_ok=True)
    
    # Initialize TASKS.md
    tasks_path = os.path.join(sub_dir, "TASKS.md")
    if not os.path.exists(tasks_path):
        with open(tasks_path, "w") as f:
            f.write(f"# {name} Task Board\n\n")
            f.write("## Strategic Vision\n")
            f.write(f"{goal}\n\n")
            f.write("## Active Tasks\n")
            f.write("- [x] Initialize sub-project structure (Agent: lead) - Status: Done\n\n")
            f.write("## Backlog\n")
            f.write("- [ ] Define roadmap for {name}\n")
            f.write("- [ ] Implement first sub-project feature\n")
        log(f"Created {tasks_path}")
    
    # Initialize .project_goal
    goal_path = os.path.join(sub_dir, ".project_goal")
    if not os.path.exists(goal_path):
        with open(goal_path, "w") as f:
            f.write(goal + "\n")
        log(f"Created {goal_path}")
        
    # Initialize BILLING.md
    billing_path = os.path.join(sub_dir, "BILLING.md")
    if not os.path.exists(billing_path):
        with open(billing_path, "w") as f:
            f.write(f"# {name} Billing & Token Usage\n\n")
            f.write("## Summary\n")
            f.write("- **Total Estimated Cost:** $0.0000\n")
            f.write("- **Total Tokens:** 0\n")
            f.write(f"- **Last Updated:** {datetime.now().strftime('%Y-%m-%d')}\n\n")
            f.write("## Usage Log\n")
            f.write("| Date | Agent | Tokens (In/Out) | Estimated Cost | Task |\n")
            f.write("|------|-------|-----------------|----------------|------|\n")
            f.write(f"| {datetime.now().strftime('%Y-%m-%d')} | lead | N/A | $0.00 | Initialized sub-project |\n")
        log(f"Created {billing_path}")

    # Initialize CHANGELOG.md
    changelog_path = os.path.join(sub_dir, "CHANGELOG.md")
    if not os.path.exists(changelog_path):
        with open(changelog_path, "w") as f:
            f.write(f"# {name} Changelog\n\n")
            f.write(f"## [Unreleased] - {datetime.now().strftime('%Y-%m-%d')}\n")
            f.write("- **Initialization:** Created sub-project structure.\n")
        log(f"Created {changelog_path}")

    # README for the sub-project
    readme_path = os.path.join(sub_dir, "README.md")
    if not os.path.exists(readme_path):
        with open(readme_path, "w") as f:
            f.write(f"# {name} Sub-Project\n\n")
            f.write(f"## Overview\n{goal}\n\n")
            f.write("## Parent Project\nJBot (Root)\n\n")
            f.write("## Operational Guide\n")
            f.write("This project is managed by JBot agents. To run an agent for this project:\n\n")
            f.write("1. Ensure the agent is defined in your Home Manager configuration.\n")
            f.write("2. The `projectDir` should point to this directory.\n")
            f.write("3. Use `systemctl --user start jbot-agent-<name>` to trigger a run.\n\n")
            f.write("## Hierarchy\n")
            if supervisor:
                f.write(f"- **Supervisor Agent:** {supervisor}\n")
            f.write(f"- **Project Directory:** `{os.path.abspath(sub_dir)}`\n")
        log(f"Created {readme_path}")

    # README for directives
    dir_readme = os.path.join(sub_dir, ".jbot", "directives", "README.md")
    if not os.path.exists(dir_readme):
        with open(dir_readme, "w") as f:
            f.write("# Sub-Project Directives\n\n")
            f.write("This directory contains formal directives specific to this sub-project.\n")

    log(f"Successfully initialized sub-project '{name}' at {sub_dir}")
    log(f"--- ACTION REQUIRED ---")
    log(f"Update your Home Manager configuration (jbot.nix) to include this sub-project:")
    log(f"")
    log(f"  programs.jbot.agents.\"{name.lower()}\" = {{")
    log(f"    enable = true;")
    log(f"    role = \"Sub-Lead\";")
    log(f"    projectDir = \"{os.path.abspath(sub_dir)}\";")
    if supervisor:
        log(f"    supervisor = \"{supervisor}\";")
    log(f"  }};")
    log(f"")
    log(f"Then run: home-manager switch")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize a JBot Sub-Project structure.")
    parser.add_argument("name", help="Name of the sub-project directory.")
    parser.add_argument("-d", "--dir", default=".", help="Parent directory (default: current directory).")
    parser.add_argument("-g", "--goal", default="A sub-project of JBot.", help="Strategic goal for the sub-project.")
    parser.add_argument("-s", "--supervisor", help="Optional: Name of the supervisor agent.")
    args = parser.parse_args()
    
    init_subproject(args.name, parent_dir=args.dir, goal=args.goal, supervisor=args.supervisor)
