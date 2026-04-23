import os
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

    # Just ensure it runs without crashing
    rotation.perform_rotations(str(tmp_path))
