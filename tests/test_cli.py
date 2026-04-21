import os
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
    tasks_file.write_text(
        "## Strategic Vision\nVision\n## Active Tasks\n- [ ] Task 1\n## Backlog\n- [ ] Backlog 1"
    )

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
    log_file.write_text(
        json.dumps({"agent": "tester", "content": {"summary": "Verified stuff"}}) + "\n"
    )

    jbot_cli.get_logs(str(tmp_path))
    captured = capsys.readouterr()
    assert "[tester] Verified stuff" in captured.out


def test_get_messages(tmp_path, capsys):
    msgs_dir = tmp_path / ".jbot" / "messages"
    msgs_dir.mkdir(parents=True)
    (msgs_dir / "2026-04-20_test.txt").write_text(
        "From: ceo\nSubject: Hello\n\nContent"
    )

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

    # Old command
    with patch(
        "sys.argv",
        ["jbot-cli.py", "-d", str(tmp_path), "add-task", "New Task", "-a", "lead"],
    ):
        jbot_cli.main()

    captured = capsys.readouterr()
    assert "Successfully added task: New Task" in captured.out
    assert "- [ ] **New Task** (Agent: lead)" in tasks_file.read_text()

    # New command structure
    with patch(
        "sys.argv",
        ["jbot-cli.py", "-d", str(tmp_path), "task", "add", "Backlog Task", "-b"],
    ):
        jbot_cli.main()

    captured = capsys.readouterr()
    assert "Successfully added task: Backlog Task" in captured.out
    assert "## Backlog" in tasks_file.read_text()
    assert "- [ ] **Backlog Task**" in tasks_file.read_text()


def test_cli_task_list(tmp_path, capsys):
    tasks_file = tmp_path / "TASKS.md"
    tasks_file.write_text("## Active Tasks\n- [ ] Task A\n## Backlog\n- [ ] Task B")

    with patch("sys.argv", ["jbot-cli.py", "-d", str(tmp_path), "task", "list"]):
        jbot_cli.main()

    captured = capsys.readouterr()
    assert "Task A" in captured.out
    assert "Task B" in captured.out


def test_cli_task_update_and_done(tmp_path, capsys):
    tasks_file = tmp_path / "TASKS.md"
    tasks_file.write_text("## Active Tasks\n- [ ] **Initial Task**")

    # Update
    with patch(
        "sys.argv",
        [
            "jbot-cli.py",
            "-d",
            str(tmp_path),
            "task",
            "update",
            "Initial",
            "-t",
            "Updated",
        ],
    ):
        jbot_cli.main()

    captured = capsys.readouterr()
    assert "Successfully updated task matching: Initial" in captured.out
    assert "Updated" in tasks_file.read_text()

    # Done
    with patch(
        "sys.argv",
        ["jbot-cli.py", "-d", str(tmp_path), "task", "done", "Updated"],
    ):
        jbot_cli.main()

    captured = capsys.readouterr()
    assert "Successfully completed task matching: Updated" in captured.out
    assert "- [x] **Updated**" in tasks_file.read_text()


def test_cli_version(tmp_path, capsys):
    version_file = tmp_path / "VERSION"
    version_file.write_text("1.0.0")

    # Show version
    with patch("sys.argv", ["jbot-cli.py", "-d", str(tmp_path), "version", "show"]):
        jbot_cli.main()
    captured = capsys.readouterr()
    assert "Current JBot Version: v1.0.0" in captured.out

    # Bump version
    with patch(
        "sys.argv", ["jbot-cli.py", "-d", str(tmp_path), "version", "bump", "minor"]
    ):
        jbot_cli.main()
    captured = capsys.readouterr()
    assert "Successfully bumped version to: v1.1.0" in captured.out
    assert version_file.read_text() == "1.1.0"

    # Tag version (mocking subprocess.run)
    with patch("subprocess.run") as mock_run:
        with patch("sys.argv", ["jbot-cli.py", "-d", str(tmp_path), "version", "tag"]):
            jbot_cli.main()
        mock_run.assert_called_once()
        assert "v1.1.0" in mock_run.call_args[0][0]
        captured = capsys.readouterr()
        assert "Creating git tag: v1.1.0" in captured.out


def test_cli_version_release(tmp_path, capsys):
    version_file = tmp_path / "VERSION"
    version_file.write_text("1.1.0")
    # Need .project_goal to find project root in main()
    (tmp_path / ".project_goal").write_text("Vision")

    with patch("subprocess.run") as mock_run:
        with patch(
            "sys.argv",
            ["jbot-cli.py", "-d", str(tmp_path), "version", "release", "patch"],
        ):
            jbot_cli.main()

        # Should have called:
        # 1. git status (is_git_clean)
        # 2. git add VERSION CHANGELOG.md
        # 3. git commit -m "chore: release v1.1.1"
        # 4. git tag -a v1.1.1 -m "Release v1.1.1"
        assert mock_run.call_count == 4
        assert version_file.read_text() == "1.1.1"
        captured = capsys.readouterr()
        assert "Successfully released v1.1.1" in captured.out
