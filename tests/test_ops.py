import os
import json
import pytest
from datetime import datetime
import sys
import importlib
from unittest.mock import patch

# Ensure scripts directory is in sys.path
sys.path.append(os.path.join(os.getcwd(), "scripts"))

def test_purge_main(tmp_path):
    jbot_purge = importlib.import_module("jbot-purge")
    dir_path = tmp_path / "directives"
    dir_path.mkdir()
    (dir_path / "002_2000-01-01_old.txt").write_text("Old")
    
    with patch("sys.argv", ["jbot-purge.py", "-d", str(dir_path), "-a", str(dir_path / "archive")]), \
         patch("jbot_utils.read_file", side_effect=lambda p, d="": open(p).read() if os.path.exists(p) else d):
        jbot_purge.main()
    
    assert (dir_path / "archive" / "002_2000-01-01_old.txt").exists()

def test_rotate_memory_main(tmp_path):
    jbot_rotate = importlib.import_module("jbot-rotate")
    log_file = tmp_path / "memory.log"
    archive_log = tmp_path / "memory.log.archive"
    
    content = "".join([json.dumps({"i": i}) + "\n" for i in range(20)])
    log_file.write_text(content)
    
    with patch("sys.argv", ["jbot-rotate.py", "-m", str(log_file), "-a", str(archive_log), "-l", "10"]):
        jbot_rotate.main()
    
    assert archive_log.exists()
    assert len(log_file.read_text().strip().split("\n")) == 10

def test_rotate_tasks_main(tmp_path):
    jbot_rotate_tasks = importlib.import_module("jbot-rotate-tasks")
    tasks_file = tmp_path / "TASKS.md"
    archive_file = tmp_path / "TASKS.archive.md"
    tasks_file.write_text("## Strategic Vision\nVision\n## Active Tasks\n- [ ] Active\n## Completed Tasks\n" + "\n".join([f"- [x] Done {i}" for i in range(20)]))
    
    with patch("sys.argv", ["jbot-rotate-tasks.py", "-t", str(tasks_file), "-a", str(archive_file), "-l", "5"]):
        jbot_rotate_tasks.main()
    
    assert archive_file.exists()
    # Check that we kept exactly 5 completed tasks
    content = tasks_file.read_text()
    completed_lines = [l for l in content.split("\n") if l.strip().startswith("- [x]")]
    assert len(completed_lines) == 5

def test_rotate_messages_main(tmp_path):
    jbot_rotate_messages = importlib.import_module("jbot-rotate-messages")
    msgs_dir = tmp_path / "messages"
    msgs_dir.mkdir()
    archive_dir = msgs_dir / "archive"
    for i in range(20):
        (msgs_dir / f"msg_{i:03}.txt").write_text("Content")
    
    with patch("sys.argv", ["jbot-rotate-messages.py", "-m", str(msgs_dir), "-a", str(archive_dir), "-l", "5"]):
        jbot_rotate_messages.main()
    
    assert archive_dir.exists()
    assert len(os.listdir(archive_dir)) == 15
    # Check that 5 remain in msgs_dir
    msgs_left = [f for f in os.listdir(msgs_dir) if os.path.isfile(os.path.join(msgs_dir, f))]
    assert len(msgs_left) == 5
