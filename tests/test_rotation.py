import os
import json
import sys
from unittest.mock import patch

# Ensure scripts directory is in sys.path
sys.path.append(os.path.join(os.getcwd(), "scripts"))
import jbot_rotation as rotation


def test_purge_directives(tmp_path):
    dir_path = tmp_path / "directives"
    dir_path.mkdir()
    archive_path = tmp_path / "archive"

    # By filename
    (dir_path / "001_2000-01-01_expired.txt").write_text("Expired")
    # By content
    (dir_path / "002_active.txt").write_text("Expiration: 2000-01-01")
    # Normal active
    (dir_path / "003_2099-01-01_active.txt").write_text("Active")

    count = rotation.purge_directives(str(dir_path), str(archive_path))
    assert count == 2
    assert (archive_path / "001_2000-01-01_expired.txt").exists()

    # Test directory skipping (must end with .txt to get past filter)
    (dir_path / "subdir.txt").mkdir()
    rotation.purge_directives(str(dir_path), str(archive_path))

    # Test empty file
    (dir_path / "empty.txt").write_text("")
    rotation.purge_directives(str(dir_path), str(archive_path))

    # Test collision in archive
    (dir_path / "001_2000-01-01_expired.txt").write_text("Expired again")
    rotation.purge_directives(str(dir_path), str(archive_path))
    assert any("001_2000-01-01_expired_" in f for f in os.listdir(archive_path))

    # Error cases
    assert rotation.purge_directives("nonexistent", "archive") == 0
    with patch("jbot_core.read_file", side_effect=Exception("Error")):
        rotation.purge_directives(str(dir_path), str(archive_path))


def test_rotate_memory(tmp_path):
    log_file = tmp_path / "memory.log"
    archive_file = tmp_path / "memory.log.archive"

    content = "".join([json.dumps({"i": i}) + "\n" for i in range(20)])
    log_file.write_text(content)

    # Limit not reached
    rotation.rotate_memory(str(log_file), str(archive_file), limit=30)
    assert not archive_file.exists()

    # Rotate
    success = rotation.rotate_memory(str(log_file), str(archive_file), limit=10)
    assert success is True
    assert len(log_file.read_text().strip().split("\n")) == 10
    assert archive_file.exists()

    # Error cases
    assert rotation.rotate_memory("nonexistent", "archive") is False
    with patch("builtins.open", side_effect=Exception("Error")):
        assert rotation.rotate_memory(str(log_file), str(archive_file)) is False


def test_rotate_tasks(tmp_path):
    tasks_file = tmp_path / "TASKS.md"
    archive_file = tmp_path / "TASKS.archive.md"

    tasks_file.write_text("""
## Strategic Vision
Vision
## Active Tasks
- [ ] Active Task
- [x] Done in active
## Backlog
- [x] Done in backlog
- [ ] Backlog Task without newline""")

    # Rotate with limit 1
    success = rotation.rotate_tasks(str(tasks_file), str(archive_file), limit=1)
    assert success is True
    assert archive_file.exists()
    # Check that archived tasks are in archive_file
    archive_content = archive_file.read_text()
    assert "Done in active" in archive_content

    tasks_file.write_text("""
## Strategic Vision
Vision
## Active Tasks
- [ ] Active Task without newline""")
    rotation.rotate_tasks(str(tasks_file), str(archive_file))

    # Error cases
    assert rotation.rotate_tasks("nonexistent") is False
    with patch("jbot_tasks.parse_tasks", side_effect=Exception("Error")):
        assert rotation.rotate_tasks(str(tasks_file)) is False


def test_rotate_messages(tmp_path):
    msg_dir = tmp_path / "messages"
    msg_dir.mkdir()
    archive_dir = tmp_path / "archive"

    for i in range(10):
        (msg_dir / f"m{i}.txt").write_text("msg")
    (msg_dir / "human.txt").write_text("human")

    # Limit not reached
    rotation.rotate_messages(str(msg_dir), str(archive_dir), limit=20)
    # The dir might exist but should be empty
    if os.path.exists(archive_dir):
        assert len(os.listdir(archive_dir)) == 0

    # Rotate
    success = rotation.rotate_messages(str(msg_dir), str(archive_dir), limit=5)
    assert success is True
    assert len([f for f in os.listdir(msg_dir) if f != "human.txt"]) == 5
    assert len(os.listdir(archive_dir)) == 5
    assert (msg_dir / "human.txt").exists()

    # Error cases
    assert rotation.rotate_messages("nonexistent", "archive") is False


def test_perform_rotations(tmp_path):
    jbot_dir = tmp_path / ".jbot"
    jbot_dir.mkdir()
    (jbot_dir / "directives").mkdir()
    (jbot_dir / "messages").mkdir()
    (jbot_dir / "memory.log").write_text("{}")
    (tmp_path / "TASKS.md").write_text("# Board")

    # Just ensure it runs without crashing
    rotation.perform_rotations(str(tmp_path))
