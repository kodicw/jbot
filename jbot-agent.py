import os
import sys
import json
import subprocess
import tempfile
import re
from datetime import datetime

def log(msg):
    print(f"[{datetime.now()}] JBot: {msg}")

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

def main():
    agent_name = os.environ.get("AGENT_NAME")
    agent_role = os.environ.get("AGENT_ROLE")
    agent_desc = os.environ.get("AGENT_DESCRIPTION")
    project_dir = os.environ.get("PROJECT_DIR")
    prompt_file = os.environ.get("PROMPT_FILE")
    gemini_pkg = os.environ.get("GEMINI_PACKAGE", "gemini")
    
    if not all([agent_name, agent_role, project_dir, prompt_file]):
        print("Error: Missing required environment variables.")
        sys.exit(1)

    os.chdir(project_dir)
    
    # Setup directories
    os.makedirs(".jbot/queues", exist_ok=True)
    os.makedirs(".jbot/memory", exist_ok=True)
    os.makedirs(".jbot/messages", exist_ok=True)
    os.makedirs(".jbot/directives", exist_ok=True)

    log(f"({agent_name}): Starting execution loop as {agent_role}...")

    # Find core files upwards
    tasks_path = find_file_upwards("TASKS.md", project_dir) or "TASKS.md"
    billing_path = find_file_upwards("BILLING.md", project_dir) or "BILLING.md"
    goal_path = find_file_upwards(".project_goal", project_dir) or ".project_goal"
    changelog_path = find_file_upwards("CHANGELOG.md", project_dir) or "CHANGELOG.md"

    # Automated Purging & Rotation
    if os.path.exists("jbot-purge.py"):
        try:
            log(f"({agent_name}): Running automated directive purging...")
            subprocess.run(["python3", "jbot-purge.py"], check=True)
        except Exception as e:
            log(f"Error running purging: {e}")
            
    if os.path.exists("jbot-rotate.py"):
        try:
            log(f"({agent_name}): Running automated memory rotation...")
            subprocess.run(["python3", "jbot-rotate.py"], check=True)
        except Exception as e:
            log(f"Error running rotation: {e}")

    # Consolidation
    lock_dir = ".jbot/lock"
    try:
        os.mkdir(lock_dir)
        queues_dir = ".jbot/queues"
        memory_log = ".jbot/memory.log"
        for q_file in os.listdir(queues_dir):
            if q_file.endswith(".json"):
                q_path = os.path.join(queues_dir, q_file)
                other_agent = q_file[:-5]
                log(f"({agent_name}): Consolidating memory from {other_agent}...")
                try:
                    with open(q_path, "r") as f:
                        content = json.load(f)
                    with open(memory_log, "a") as f:
                        f.write(json.dumps({"agent": other_agent, "content": content}) + "\n")
                    os.remove(q_path)
                except Exception as e:
                    log(f"Error consolidating {q_path}: {e}")
        os.rmdir(lock_dir)
    except FileExistsError:
        pass # Another agent is consolidating

    # Prepare Context
    tree = subprocess.check_output(["find", ".", "-maxdepth", "2", "-not", "-path", "*/.*"], text=True).strip()
    
    goal = "Maintain and improve the JBot project infrastructure."
    if os.path.exists(goal_path):
        with open(goal_path, "r") as f:
            goal = f.read().strip()

    rag_formatted = "No previous memory found."
    if os.path.exists(".jbot/memory.log"):
        with open(".jbot/memory.log", "r") as f:
            lines = f.readlines()
            rag_entries = []
            for line in lines[-20:]:
                try:
                    data = json.loads(line)
                    rag_entries.append(f"[{data.get('agent')}] {data.get('content', {}).get('summary')}")
                except:
                    rag_entries.append(line.strip())
            rag_formatted = "\n".join(rag_entries[-10:])

    task_board = f"No Task Board found at {tasks_path}. Please initialize it if needed."
    if os.path.exists(tasks_path):
        with open(tasks_path, "r") as f:
            task_board = f.read()

    # Team Registry (Enhanced for hierarchy)
    team_registry = "No team registry found."
    if os.path.exists(".jbot/agents.json"):
        with open(".jbot/agents.json", "r") as f:
            agents = json.load(f)
            registry_sections = {
                "Teammates": [],
                "Supervisors (Parent Projects)": [],
                "Sub-projects (Nested Agents)": []
            }
            
            curr_pd = os.path.abspath(project_dir)
            
            for name, info in agents.items():
                if name == agent_name: continue
                
                agent_pd = os.path.abspath(info.get('projectDir', curr_pd))
                role_info = f"- {name}: {info.get('role')} ({info.get('description')})"
                if info.get("supervisor"):
                    role_info += f" [Supervisor: {info.get('supervisor')}]"
                
                if agent_pd == curr_pd:
                    registry_sections["Teammates"].append(role_info)
                elif curr_pd.startswith(agent_pd):
                    registry_sections["Supervisors (Parent Projects)"].append(f"{role_info} [Dir: {agent_pd}]")
                elif agent_pd.startswith(curr_pd):
                    registry_sections["Sub-projects (Nested Agents)"].append(f"{role_info} [Dir: {agent_pd}]")
                else:
                    # Should not happen with current filter, but for safety:
                    registry_sections["Teammates"].append(role_info)
            
            registry_lines = []
            for section, lines in registry_sections.items():
                if lines:
                    registry_lines.append(f"### {section}")
                    registry_lines.extend(lines)
            
            team_registry = "\n".join(registry_lines) if registry_lines else "No other agents in visibility."

    # Messages
    messages = "No recent messages."
    msgs_dir = ".jbot/messages"
    if os.path.exists(msgs_dir):
        msg_files = sorted(os.listdir(msgs_dir))
        if msg_files:
            msg_list = []
            for mf in msg_files[-5:]: # Last 5 messages
                with open(os.path.join(msgs_dir, mf), "r") as f:
                    msg_list.append(f"--- Message {mf} ---\n{f.read()}")
            messages = "\n".join(msg_list)

    # Formal Directives
    directives = "No formal directives."
    dir_path = ".jbot/directives"
    if os.path.exists(dir_path):
        dir_files = sorted([f for f in os.listdir(dir_path) if f.endswith((".txt", ".md")) and f != "README.md"])
        if dir_files:
            dir_list = []
            today = datetime.now().strftime("%Y-%m-%d")
            for df in dir_files:
                is_expired = False
                # Try to find a date (YYYY-MM-DD) in the filename
                date_match = re.search(r"(\d{4}-\d{2}-\d{2})", df)
                exp_date_from_filename = date_match.group(1) if date_match else None
                
                try:
                    with open(os.path.join(dir_path, df), "r") as f:
                        directive_content = f.read()
                        
                        # Check for explicit expiration in content: "Expiration: YYYY-MM-DD"
                        content_exp_match = re.search(r"Expiration:\s*(\d{4}-\d{2}-\d{2})", directive_content, re.IGNORECASE)
                        if content_exp_match:
                            exp_date = content_exp_match.group(1)
                            if today > exp_date:
                                is_expired = True
                                log(f"({agent_name}): Directive {df} has expired (from content).")
                        elif exp_date_from_filename:
                            if today > exp_date_from_filename:
                                is_expired = True
                                log(f"({agent_name}): Directive {df} has expired (from filename).")
                        
                        if not is_expired:
                            dir_list.append(f"--- Directive {df} ---\n{directive_content}")
                except Exception as e:
                    log(f"Error reading directive {df}: {e}")
            
            if dir_list:
                directives = "\n".join(dir_list)

    # Read and replace prompt
    with open(prompt_file, "r") as f:
        prompt_content = f.read()

    replacements = {
        "{AGENT_NAME}": agent_name,
        "{AGENT_ROLE}": agent_role,
        "{AGENT_DESCRIPTION}": agent_desc,
        "{PROJECT_GOAL}": goal,
        "{DIRECTORY_TREE}": tree,
        "{RAG_DATABASE_RESULTS}": rag_formatted,
        "{TASK_BOARD}": task_board,
        "{TEAM_REGISTRY}": team_registry,
        "{MESSAGES}": messages,
        "{DIRECTIVES}": directives
    }

    for k, v in replacements.items():
        prompt_content = prompt_content.replace(k, str(v))

    with tempfile.NamedTemporaryFile(mode="w", delete=False) as tf:
        tf.write(prompt_content)
        prepared_prompt_path = tf.name

    # Set up memory output for gemini
    os.environ["MEMORY_OUTPUT"] = f".jbot/queues/{agent_name}.json"

    log(f"({agent_name}): Invoking Gemini CLI...")
    
    # Capture output for token tracking while still showing real-time logs
    full_output = []
    try:
        process = subprocess.Popen([gemini_pkg, "-y", "-d", "-p", prompt_content], 
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        for line in process.stdout:
            print(line, end="", flush=True)
            full_output.append(line)
        
        process.wait()
        if process.returncode != 0:
            log(f"Error: Gemini CLI failed with exit code {process.returncode}")
            sys.exit(process.returncode)

        # Parse tokens from output
        output_text = "".join(full_output)
        input_tokens = 0
        output_tokens = 0
        
        # More robust regex for tokens
        token_match = re.search(r"(\d+(?:,\d+)*)\s*input tokens,\s*(\d+(?:,\d+)*)\s*output tokens", output_text)
        if not token_match:
            # Try a simpler match if the first one fails
            token_match = re.search(r"input tokens:\s*(\d+).*output tokens:\s*(\d+)", output_text, re.IGNORECASE | re.DOTALL)
            
        if token_match:
            try:
                input_tokens = int(token_match.group(1).replace(",", ""))
                output_tokens = int(token_match.group(2).replace(",", ""))
                log(f"({agent_name}): Captured usage - {input_tokens} in, {output_tokens} out.")
            except (ValueError, IndexError):
                log(f"({agent_name}): Failed to parse token counts from match.")

        # Check for TASKS.md bloat
        if os.path.exists(tasks_path):
            with open(tasks_path, "r") as f:
                task_lines = f.readlines()
                if len(task_lines) > 200:
                    log(f"WARNING ({agent_name}): {tasks_path} is getting large ({len(task_lines)} lines). Consider archiving completed tasks.")

        # Update BILLING.md
        if os.path.exists(billing_path) and os.access(billing_path, os.W_OK):
            try:
                task_name = "Automated Task"
                if os.path.exists(tasks_path):
                    with open(tasks_path, "r") as f:
                        for line in f:
                            if "In Progress" in line and f"(Agent: {agent_name})" in line:
                                parts = line.split("] ")
                                if len(parts) > 1:
                                    task_name = parts[1].split(" (Agent:")[0].strip()
                                break
                
                today_str = datetime.now().strftime("%Y-%m-%d")
                total_tokens = input_tokens + output_tokens
                # Dummy cost calculation: $1.00 per 1M tokens
                cost = (total_tokens / 1_000_000) * 1.0
                
                with open(billing_path, "a") as f:
                    f.write(f"| {today_str} | {agent_name} | {input_tokens}/{output_tokens} | ${cost:.4f} | {task_name} |\n")
                
                log(f"({agent_name}): Updated {billing_path}")
            except Exception as e:
                log(f"Error updating billing: {e}")

        # Update Dashboard
        if os.path.exists("jbot-dashboard.py"):
            try:
                log(f"({agent_name}): Updating INDEX.md dashboard...")
                subprocess.run(["python3", "jbot-dashboard.py"], check=True)
            except Exception as e:
                log(f"Error updating dashboard: {e}")

    except Exception as e:
        log(f"Error: Execution failed: {e}")
        sys.exit(1)
    finally:
        if os.path.exists(prepared_prompt_path):
            os.remove(prepared_prompt_path)

    log(f"({agent_name}): Execution loop finished.")

if __name__ == "__main__":
    main()
