import sys
import os

# Add scripts to path
sys.path.append(os.path.join(os.getcwd(), "scripts"))

import jbot_tasks as tasks
import jbot_infra as infra

content = infra.get_note_content("type:tasks")
print(f"Content length: {len(content) if content else 0}")
if content:
    print("--- Content Start ---")
    print(content[:500])
    print("--- Content End ---")

data = tasks.parse_tasks()
print(f"Active tasks: {len(data['active'])}")
print(f"Done count: {data['done_count']}")
print(f"Vision: {data['vision']}")
