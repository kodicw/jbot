import os
import re
import argparse
from datetime import datetime

def log(msg):
    print(f"[{datetime.now()}] JBot Task Rotate: {msg}")

def rotate_tasks(tasks_file="TASKS.md", archive_file="TASKS.archive.md", limit=20):
    if not os.path.exists(tasks_file):
        log(f"Tasks file {tasks_file} not found.")
        return

    try:
        with open(tasks_file, "r") as f:
            lines = f.readlines()
        
        sections = {
            "header": [],
            "vision": [],
            "active": [],
            "backlog": [],
            "completed": []
        }
        
        current_section = "header"
        
        for line in lines:
            if line.startswith("## Strategic Vision"):
                current_section = "vision"
            elif line.startswith("## Active Tasks"):
                current_section = "active"
            elif line.startswith("## Backlog"):
                current_section = "backlog"
            elif line.startswith("## Completed Tasks"):
                current_section = "completed"
            
            sections[current_section].append(line)

        # Ensure headers exist even if section was missing
        if not sections["vision"]: sections["vision"] = ["## Strategic Vision (CEO)\n"]
        if not sections["active"]: sections["active"] = ["## Active Tasks\n"]
        if not sections["backlog"]: sections["backlog"] = ["## Backlog\n"]
        if not sections["completed"]: sections["completed"] = ["## Completed Tasks\n"]

        # 1. Move [x] tasks from active and backlog to completed
        new_active = [sections["active"][0]] # Keep header
        new_backlog = [sections["backlog"][0]] # Keep header
        newly_completed = []

        for line in sections["active"][1:]:
            if "[x]" in line:
                newly_completed.append(line)
            elif line.strip() == "" or line.strip() == "...":
                continue
            else:
                new_active.append(line)

        for line in sections["backlog"][1:]:
            if "[x]" in line:
                newly_completed.append(line)
            elif line.strip() == "" or line.strip() == "...":
                continue
            else:
                new_backlog.append(line)

        # 2. Update Completed Tasks section
        # Remove literal "..." if present
        current_completed = [l for l in sections["completed"][1:] if l.strip() != "..."]
        
        # Combine existing completed and newly completed
        all_completed = current_completed + newly_completed
        
        to_keep = all_completed
        to_archive = []
        
        if len(all_completed) > limit:
            to_keep = all_completed[-limit:]
            to_archive = all_completed[:-limit]
            log(f"Archiving {len(to_archive)} tasks from Completed Tasks.")

        # 3. Write Archive
        if to_archive:
            with open(archive_file, "a") as f:
                if not os.path.exists(archive_file) or os.path.getsize(archive_file) == 0:
                    f.write("# JBot Task Archive\n\n")
                f.write(f"## Archived on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.writelines(to_archive)
                f.write("\n")

        # 4. Rewrite TASKS.md
        with open(tasks_file, "w") as f:
            if not sections["header"]:
                f.write("# JBot Task Board\n\n")
            else:
                f.writelines(sections["header"])
            
            f.writelines(sections["vision"])
            f.write("\n")
            f.writelines(new_active)
            if not new_active[-1].endswith("\n"): f.write("\n")
            f.write("\n")
            f.writelines(new_backlog)
            if not new_backlog[-1].endswith("\n"): f.write("\n")
            f.write("\n")
            f.writelines(sections["completed"][:1]) # Write completed header
            f.writelines(to_keep)
        
        log(f"Successfully rotated tasks. TASKS.md now has {len(to_keep)} completed tasks.")

    except Exception as e:
        log(f"Error rotating tasks: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="JBot Task Rotation Tool")
    parser.add_argument("-t", "--tasks", default="TASKS.md", help="Tasks file")
    parser.add_argument("-a", "--archive", default="TASKS.archive.md", help="Archive tasks file")
    parser.add_argument("-l", "--limit", type=int, default=10, help="Max entries to keep in Completed Tasks")
    args = parser.parse_args()
    
    rotate_tasks(tasks_file=args.tasks, archive_file=args.archive, limit=args.limit)
