import os
import json
from datetime import datetime
import sys
from unittest.mock import patch, MagicMock
import subprocess
import pytest

# Ensure scripts directory is in sys.path
sys.path.append(os.path.join(os.getcwd(), "scripts"))
import jbot_utils as utils


def test_log(capsys):
    utils.log("Test Message", "TestComponent")
    captured = capsys.readouterr()
    assert "TestComponent: Test Message" in captured.out


def test_find_file_upwards(tmp_path):
    # Create a file in a parent directory
    parent_dir = tmp_path / "parent"
    parent_dir.mkdir()
    target_file = parent_dir / "target.txt"
    target_file.write_text("Found")

    child_dir = parent_dir / "child"
    child_dir.mkdir()

    found = utils.find_file_upwards("target.txt", str(child_dir))
    assert found == str(target_file)

    not_found = utils.find_file_upwards("nonexistent.txt", str(child_dir))
    assert not_found is None


def test_get_project_root(tmp_path):
    goal_file = tmp_path / ".project_goal"
    goal_file.write_text("Goal")

    child_dir = tmp_path / "child"
    child_dir.mkdir()

    root = utils.get_project_root(str(child_dir))
    assert root == str(tmp_path)

    # Test fallback
    root_fallback = utils.get_project_root("/non/existent/path")
    assert root_fallback == "/non/existent/path"


def test_load_json(tmp_path):
    json_file = tmp_path / "data.json"
    data = {"key": "value"}
    json_file.write_text(json.dumps(data))

    loaded = utils.load_json(str(json_file))
    assert loaded == data

    # Test default
    assert utils.load_json("nonexistent.json", default={"a": 1}) == {"a": 1}


def test_load_json_error():
    with patch("builtins.open", side_effect=Exception("Read Error")):
        assert utils.load_json("some.json", default={"err": 1}) == {"err": 1}


def test_save_json(tmp_path):
    json_file = tmp_path / "subdir" / "output.json"
    data = {"hello": "world"}
    utils.save_json(str(json_file), data)

    with open(json_file, "r") as f:
        assert json.load(f) == data


def test_save_json_error():
    with patch("os.makedirs", side_effect=Exception("Write Error")):
        # Should log and return gracefully
        utils.save_json("some.json", {})


def test_read_file(tmp_path):
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("Hello World")
    assert utils.read_file(str(txt_file)) == "Hello World"
    assert utils.read_file("nonexistent.txt", "Default") == "Default"


def test_read_file_error():
    with patch("builtins.open", side_effect=Exception("Read Error")):
        assert utils.read_file("some.txt", "Fallback") == "Fallback"


def test_write_file(tmp_path):
    txt_file = tmp_path / "output.txt"
    utils.write_file(str(txt_file), "Content")
    assert txt_file.read_text() == "Content"

    with patch("os.makedirs", side_effect=Exception("Write Error")):
        assert utils.write_file("some.txt", "Content") is False


def test_is_git_clean():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="")
        assert utils.is_git_clean() is True

        mock_run.return_value = MagicMock(stdout="M file.txt")
        assert utils.is_git_clean() is False
        
    with patch("subprocess.run", side_effect=Exception("git error")):
        assert utils.is_git_clean() is False


def test_parse_tasks(tmp_path):
    tasks_file = tmp_path / "TASKS.md"
    tasks_file.write_text("""
## Strategic Vision
Goal: Excellence.

## Active Tasks
- [ ] **Task 1** (Agent: test)
- [ ] **Task 2**

## Backlog
- [ ] **Backlog 1**

## Completed Tasks
- [x] **Task 3**
""")

    data = utils.parse_tasks(str(tasks_file))
    assert data["vision"] == "Goal: Excellence."
    assert "- [ ] **Task 1** (Agent: test)" in data["active"]
    assert "- [ ] **Backlog 1**" in data["backlog"]
    assert data["done_count"] == 1

    assert utils.parse_tasks("nonexistent.md")["active"] == []


def test_add_task(tmp_path):
    tasks_file = tmp_path / "TASKS.md"
    tasks_file.write_text("## Strategic Vision\nGoal\n")

    # Test add when Active Tasks section missing
    utils.add_task(str(tasks_file), "New Task")
    content = tasks_file.read_text()
    assert "## Active Tasks" in content
    assert "- [ ] **New Task**" in content

    # Test add when Active Tasks section exists
    utils.add_task(str(tasks_file), "Second Task", agent="lead")
    content = tasks_file.read_text()
    assert "- [ ] **Second Task** (Agent: lead)" in content

    # Test add to backlog
    utils.add_task(str(tasks_file), "Backlog Task", backlog=True)
    content = tasks_file.read_text()
    assert "## Backlog" in content
    assert "- [ ] **Backlog Task**" in content


def test_update_task(tmp_path):
    tasks_file = tmp_path / "TASKS.md"
    tasks_file.write_text("""
## Active Tasks
- [ ] **Old Task** (Agent: lead)
## Backlog
- [ ] **Wait Task**
""")

    # Update text and agent
    utils.update_task(
        str(tasks_file), "Old Task", new_text="Updated Task", agent="tester"
    )
    content = tasks_file.read_text()
    assert "- [ ] **Updated Task** (Agent: tester)" in content
    assert "Old Task" not in content

    # Move to backlog
    utils.update_task(str(tasks_file), "Updated Task", move_to="backlog")
    data = utils.parse_tasks(str(tasks_file))
    assert any("Updated Task" in t for t in data["backlog"])
    assert not any("Updated Task" in t for t in data["active"])

    # Move from backlog to active
    utils.update_task(str(tasks_file), "Wait Task", move_to="active")
    data = utils.parse_tasks(str(tasks_file))
    assert any("Wait Task" in t for t in data["active"])


def test_complete_task(tmp_path):
    tasks_file = tmp_path / "TASKS.md"
    tasks_file.write_text("""
## Active Tasks
- [ ] **Working Task**
## Completed Tasks
""")

    utils.complete_task(str(tasks_file), "Working Task")
    content = tasks_file.read_text()
    assert "- [x] **Working Task**" in content
    assert "## Completed Tasks\n- [x] **Working Task**" in content
    assert "- [ ] **Working Task**" not in content


def test_add_task_missing_file():
    assert utils.add_task("nonexistent.md", "Task") is False


def test_get_team_registry(tmp_path):
    jbot_dir = tmp_path / ".jbot"
    jbot_dir.mkdir()
    agents_file = jbot_dir / "agents.json"
    data = {"agent1": {"role": "Tester"}}
    agents_file.write_text(json.dumps(data))

    registry = utils.get_team_registry(str(tmp_path))
    assert registry == data


def test_get_recent_messages(tmp_path):
    msgs_dir = tmp_path / "messages"
    msgs_dir.mkdir()
    (msgs_dir / "2026-04-20_12-00-00_ceo.txt").write_text("MSG 1")

    msgs = utils.get_recent_messages(str(msgs_dir), count=5)
    assert len(msgs) == 1

    assert utils.get_recent_messages("nonexistent_dir") == []


def test_get_recent_logs(tmp_path):
    log_file = tmp_path / "memory.log"
    log_file.write_text(
        json.dumps({"agent": "a1", "content": {"summary": "s1"}}) + "\n"
    )
    with open(log_file, "a") as f:
        f.write(json.dumps({"agent": "a2", "content": {"summary": "s2"}}) + "\n")

    logs = utils.get_recent_logs(str(log_file), count=1)
    assert len(logs) == 1
    assert logs[0]["agent"] == "a2"

    assert utils.get_recent_logs("nonexistent.log") == []


def test_parse_directives(tmp_path):
    dir_path = tmp_path / "directives"
    dir_path.mkdir()

    today = datetime.now().strftime("%Y-%m-%d")
    (dir_path / f"999_{today}_future.txt").write_text("Future Directive")
    (dir_path / "001_2000-01-01_expired.txt").write_text("Expired Directive")
    (dir_path / "002_active.txt").write_text("Active Directive\nExpiration: 2099-01-01")
    (dir_path / "003_expired_content.txt").write_text(
        "Expired content\nExpiration: 2000-01-01"
    )

    directives = utils.parse_directives(str(dir_path))
    filenames = [d["filename"] for d in directives]
    assert f"999_{today}_future.txt" in filenames
    assert "001_2000-01-01_expired.txt" not in filenames
    assert "002_active.txt" in filenames
    assert "003_expired_content.txt" not in filenames

    assert utils.parse_directives("nonexistent_dir") == []


def test_versioning(tmp_path):
    version_file = tmp_path / "VERSION"
    version_file.write_text("1.0.0")

    assert utils.get_version(str(tmp_path)) == "1.0.0"

    # Bump patch
    new_v = utils.bump_version(str(tmp_path), "patch")
    assert new_v == "1.0.1"
    assert version_file.read_text() == "1.0.1"

    # Bump minor
    new_v = utils.bump_version(str(tmp_path), "minor")
    assert new_v == "1.1.0"
    assert version_file.read_text() == "1.1.0"

    # Bump major
    new_v = utils.bump_version(str(tmp_path), "major")
    assert new_v == "2.0.0"
    assert version_file.read_text() == "2.0.0"

    # Test invalid format
    version_file.write_text("invalid")
    assert utils.bump_version(str(tmp_path), "patch") is None

    # Test invalid part
    version_file.write_text("1.0.0")
    assert utils.bump_version(str(tmp_path), "invalid") is None

def test_update_changelog(tmp_path):
    changelog_file = tmp_path / "CHANGELOG.md"
    changelog_file.write_text("""
## [Unreleased]
### Added
- Feature A
## [1.0.0] - 2026-04-19
- Initial release
""")
    
    success = utils.update_changelog(str(tmp_path), "1.1.0")
    assert success is True
    content = changelog_file.read_text()
    assert "## [1.1.0]" in content
    assert "- Feature A" in content
    assert "## [Unreleased]\n\n## [1.1.0]" in content

    # Error case
    os.remove(changelog_file)
    assert utils.update_changelog(str(tmp_path), "1.2.0") is False

def test_purge_directives(tmp_path):
    dir_path = tmp_path / "directives"
    dir_path.mkdir()
    archive_path = tmp_path / "archive"
    
    (dir_path / "001_2000-01-01_expired.txt").write_text("Expired")
    (dir_path / "002_2099-01-01_active.txt").write_text("Active")
    
    count = utils.purge_directives(str(dir_path), str(archive_path))
    assert count == 1
    assert not (dir_path / "001_2000-01-01_expired.txt").exists()
    assert (archive_path / "001_2000-01-01_expired.txt").exists()

def test_rotate_memory(tmp_path):
    log_file = tmp_path / "memory.log"
    archive_file = tmp_path / "memory.log.archive"
    
    content = "".join([json.dumps({"i": i}) + "\n" for i in range(20)])
    log_file.write_text(content)
    
    success = utils.rotate_memory(str(log_file), str(archive_file), limit=10)
    assert success is True
    assert len(log_file.read_text().strip().split("\n")) == 10
    assert archive_file.exists()

def test_rotate_tasks(tmp_path):
    tasks_file = tmp_path / "TASKS.md"
    archive_file = tmp_path / "TASKS.archive.md"
    
    tasks_file.write_text("""
## Strategic Vision
Vision
## Active Tasks
- [ ] Active Task
## Completed Tasks
- [x] Done 1
- [x] Done 2
""")
    
    success = utils.rotate_tasks(str(tasks_file), str(archive_file), limit=1)
    assert success is True
    content = tasks_file.read_text()
    assert "Done 2" in content
    assert "Done 1" not in content
    assert archive_file.exists()

def test_rotate_messages(tmp_path):
    msg_dir = tmp_path / "messages"
    msg_dir.mkdir()
    archive_dir = tmp_path / "archive"
    
    for i in range(10):
        (msg_dir / f"m{i}.txt").write_text("msg")
        
    success = utils.rotate_messages(str(msg_dir), str(archive_dir), limit=5)
    assert success is True
    assert len(os.listdir(msg_dir)) == 5
    assert len(os.listdir(archive_dir)) == 5

def test_generate_dashboard(tmp_path):
    (tmp_path / ".project_goal").write_text("Vision")
    (tmp_path / "TASKS.md").write_text("## Active Tasks\n- [ ] Task")
    
    success = utils.generate_dashboard("INDEX.md", str(tmp_path))
    assert success is True
    assert (tmp_path / "INDEX.md").exists()
    content = (tmp_path / "INDEX.md").read_text()
    assert "Vision" in content
    assert "Task" in content

def test_send_message(tmp_path):
    msgs_dir = tmp_path / ".jbot" / "messages"
    msgs_dir.mkdir(parents=True)
    
    success = utils.send_message(str(tmp_path), "ceo", "hello world")
    assert success is True
    assert len(os.listdir(msgs_dir)) == 1

def test_run_maintenance(tmp_path):
    jbot_dir = tmp_path / ".jbot"
    jbot_dir.mkdir()
    queues_dir = jbot_dir / "queues"
    queues_dir.mkdir()
    (queues_dir / "tester.json").write_text(json.dumps({"summary": "done"}))
    
    success = utils.run_maintenance(str(tmp_path))
    assert success is True
    assert (jbot_dir / "memory.log").exists()
    assert not (queues_dir / "tester.json").exists()
