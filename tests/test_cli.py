import os
import pytest
from unittest.mock import patch
import sys
import importlib

# Ensure scripts directory is in sys.path
sys.path.append(os.path.join(os.getcwd(), "scripts"))
jbot_cli = importlib.import_module("jbot-cli")

def test_get_status(tmp_path, capsys):
    goal_file = tmp_path / ".project_goal"
    goal_file.write_text("Company Vision")
    tasks_file = tmp_path / "TASKS.md"
    tasks_file.write_text("## Active Tasks\n- [ ] Task 1\n- [x] Task 2")
    
    jbot_cli.get_status(str(tmp_path))
    captured = capsys.readouterr()
    assert "Company Vision" in captured.out
    assert "Task 1" in captured.out
    assert "1 tasks completed" in captured.out

def test_get_tasks(tmp_path, capsys):
    tasks_file = tmp_path / "TASKS.md"
    tasks_file.write_text("## Strategic Vision\nVision\n## Active Tasks\n- [ ] Task 1\n## Backlog\n- [ ] Backlog 1")
    
    jbot_cli.get_tasks(str(tmp_path))
    captured = capsys.readouterr()
    assert "Vision" in captured.out
    assert "Task 1" in captured.out
    assert "Backlog 1" in captured.out

def test_get_logs(tmp_path, capsys):
    import json
    jbot_dir = tmp_path / ".jbot"
    jbot_dir.mkdir()
    log_file = jbot_dir / "memory.log"
    log_file.write_text(json.dumps({"agent": "tester", "content": {"summary": "Verified stuff"}}) + "\n")
    
    jbot_cli.get_logs(str(tmp_path))
    captured = capsys.readouterr()
    assert "[tester] Verified stuff" in captured.out

def test_get_messages(tmp_path, capsys):
    msgs_dir = tmp_path / ".jbot" / "messages"
    msgs_dir.mkdir(parents=True)
    (msgs_dir / "2026-04-20_test.txt").write_text("From: ceo\nSubject: Hello\n\nContent")
    
    jbot_cli.get_messages(str(tmp_path))
    captured = capsys.readouterr()
    assert "From: ceo - Subject: Hello" in captured.out

def test_cli_main_status(tmp_path, capsys):
    (tmp_path / ".project_goal").write_text("Vision")
    (tmp_path / "TASKS.md").write_text("## Active Tasks\n- [ ] Task 1")
    
    with patch("sys.argv", ["jbot-cli.py", "-d", str(tmp_path), "status"]):
        jbot_cli.main()
    
    captured = capsys.readouterr()
    assert "Vision" in captured.out
    assert "Task 1" in captured.out

def test_cli_main_add_task(tmp_path, capsys):
    tasks_file = tmp_path / "TASKS.md"
    tasks_file.write_text("## Active Tasks\n")
    
    with patch("sys.argv", ["jbot-cli.py", "-d", str(tmp_path), "add-task", "New Task", "-a", "lead"]):
        jbot_cli.main()
    
    captured = capsys.readouterr()
    assert "Successfully added task: New Task" in captured.out
    assert "- [ ] **New Task** (Agent: lead)" in tasks_file.read_text()
