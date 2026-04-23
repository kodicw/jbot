import os
import json
from unittest.mock import patch, MagicMock
import sys
import subprocess

# Ensure scripts directory is in sys.path
sys.path.append(os.path.join(os.getcwd(), "scripts"))
import jbot_cli


def test_get_status(tmp_path, capsys):
    goal_file = tmp_path / ".project_goal"
    goal_file.write_text("Company Vision")
    tasks_file = tmp_path / "TASKS.md"
    tasks_file.write_text(
        "## Active Tasks\n- [ ] Task 1\n- [ ] Task 2\n- [ ] Task 3\n- [ ] Task 4\n- [ ] Task 5\n- [ ] Task 6\n- [x] Task 7"
    )

    jbot_cli.get_status(str(tmp_path))
    captured = capsys.readouterr()
    assert "Company Vision" in captured.out
    assert "Task 1" in captured.out
    assert "... and 1 more." in captured.out
    assert "1 tasks completed" in captured.out


def test_get_tasks(tmp_path, capsys):
    tasks_file = tmp_path / "TASKS.md"
    tasks_file.write_text(
        "## Strategic Vision\nVision\n## Active Tasks\n- [ ] Task 1\n## Backlog\n- [ ] Backlog 1"
    )

    # Standard list
    jbot_cli.get_tasks(str(tmp_path))
    captured = capsys.readouterr()
    assert "Vision" in captured.out
    assert "Task 1" in captured.out
    assert "Backlog 1" in captured.out

    # Show all
    jbot_cli.get_tasks(str(tmp_path), show_all=True)
    captured = capsys.readouterr()
    assert "## Strategic Vision" in captured.out

    # Error case - now falls back to nb
    os.remove(tasks_file)
    with patch(
        "jbot_tasks.infra.get_note_content",
        return_value="## Strategic Vision\nTechnical Excellence\n",
    ):
        jbot_cli.get_tasks(str(tmp_path))
    captured = capsys.readouterr()
    assert "JBot Task Board (nb)" in captured.out
    assert "Technical Excellence" in captured.out


def test_get_logs(tmp_path, capsys):
    jbot_dir = tmp_path / ".jbot"
    jbot_dir.mkdir()
    log_file = jbot_dir / "memory.log"
    log_file.write_text(
        json.dumps({"agent": "tester", "content": {"summary": "Verified stuff"}}) + "\n"
    )

    jbot_cli.get_logs(str(tmp_path))
    captured = capsys.readouterr()
    assert "[tester] Verified stuff" in captured.out

    # Error case - now falls back to nb
    os.remove(log_file)
    with patch(
        "jbot_infra.get_recent_logs",
        return_value=[{"agent": "tester", "content": {"summary": "Verified nb"}}],
    ):
        jbot_cli.get_logs(str(tmp_path))
        captured = capsys.readouterr()
        assert "Activity (nb)" in captured.out or "Verified nb" in captured.out


def test_get_messages(tmp_path, capsys):
    msgs_dir = tmp_path / ".jbot" / "messages"
    msgs_dir.mkdir(parents=True)
    (msgs_dir / "2026-04-20_test.txt").write_text(
        "From: ceo\nSubject: Hello\n\nContent"
    )

    jbot_cli.get_messages(str(tmp_path))
    captured = capsys.readouterr()
    assert "From: ceo - Subject: Hello" in captured.out

    # Error case
    import shutil

    shutil.rmtree(msgs_dir)
    jbot_cli.get_messages(str(tmp_path))
    captured = capsys.readouterr()
    assert "No messages directory found." in captured.out


def test_cli_main_status(tmp_path, capsys):
    (tmp_path / ".project_goal").write_text("Vision")
    (tmp_path / "TASKS.md").write_text("## Active Tasks\n- [ ] Task 1")

    with patch("sys.argv", ["jbot_cli.py", "-d", str(tmp_path), "status"]):
        jbot_cli.main()

    captured = capsys.readouterr()
    assert "Vision" in captured.out
    assert "Task 1" in captured.out


def test_cli_main_add_task(tmp_path, capsys):
    tasks_file = tmp_path / "TASKS.md"
    tasks_file.write_text("## Active Tasks\n")

    # New command structure
    with patch(
        "sys.argv",
        ["jbot_cli.py", "-d", str(tmp_path), "task", "add", "New Task", "-a", "lead"],
    ):
        jbot_cli.main()

    captured = capsys.readouterr()
    assert "Added task: New Task" in captured.out
    assert "- [ ] **New Task** (Agent: lead)" in tasks_file.read_text()

    # Backlog Task
    with patch(
        "sys.argv",
        ["jbot_cli.py", "-d", str(tmp_path), "task", "add", "Backlog Task", "-b"],
    ):
        jbot_cli.main()

    captured = capsys.readouterr()
    assert "Added task: Backlog Task" in captured.out
    assert "## Backlog" in tasks_file.read_text()
    assert "- [ ] **Backlog Task**" in tasks_file.read_text()


def test_cli_task_list(tmp_path, capsys):
    tasks_file = tmp_path / "TASKS.md"
    tasks_file.write_text("## Active Tasks\n- [ ] Task A\n## Backlog\n- [ ] Task B")

    with patch("sys.argv", ["jbot_cli.py", "-d", str(tmp_path), "task", "list"]):
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
            "jbot_cli.py",
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
    assert "Updated task: Initial" in captured.out
    assert "Updated" in tasks_file.read_text()

    # Done
    with patch(
        "sys.argv",
        ["jbot_cli.py", "-d", str(tmp_path), "task", "done", "Updated"],
    ):
        jbot_cli.main()

    captured = capsys.readouterr()
    assert "Completed task: Updated" in captured.out
    assert "- [x] **Updated**" in tasks_file.read_text()


def test_cli_human(tmp_path, capsys):
    with patch("sys.argv", ["jbot_cli.py", "-d", str(tmp_path), "human"]):
        with patch("jbot_tui.main") as mock_tui:
            jbot_cli.main()
            mock_tui.assert_called_once()


def test_cli_system(tmp_path, capsys):
    with patch("sys.argv", ["jbot_cli.py", "-d", str(tmp_path), "system", "show"]):
        with patch("jbot_cli.handle_system") as mock_sys:
            jbot_cli.main()
            mock_sys.assert_called_once_with(str(tmp_path), "show")


def test_handle_system(tmp_path, capsys):
    (tmp_path / "jbot_prompt.txt").write_text("Bootstrap")

    with patch("jbot_infra.get_note_content", return_value=None):
        jbot_cli.handle_system(str(tmp_path), "show")
        captured = capsys.readouterr()
        assert "Bootstrap" in captured.out

    with patch("jbot_infra.get_note_content", return_value="NB Prompt"):
        jbot_cli.handle_system(str(tmp_path), "show")
        captured = capsys.readouterr()
        assert "NB Prompt" in captured.out


@patch("subprocess.run")
def test_handle_system_edit(mock_run, tmp_path):
    with patch("jbot_infra.get_note_content", return_value=None):
        with patch("jbot_infra.NbClient") as mock_nb:
            jbot_cli.handle_system(str(tmp_path), "edit")
            mock_nb.return_value.add.assert_called_once()
            mock_run.assert_called_once()
            assert "jbot:edit" in mock_run.call_args[0][0]

    mock_run.reset_mock()
    with patch("jbot_infra.get_note_content", return_value="Exists"):
        with patch("jbot_infra.NbClient") as mock_nb:
            jbot_cli.handle_system(str(tmp_path), "edit")
            mock_nb.return_value.add.assert_not_called()
            mock_run.assert_called_once()


def test_cli_main_rotate(tmp_path, capsys):
    with patch("sys.argv", ["jbot_cli.py", "-d", str(tmp_path), "rotate"]):
        jbot_cli.main()
        captured = capsys.readouterr()
        assert "usage" in captured.out


def test_cli_main_task_error(tmp_path, capsys):
    pass

    with patch(
        "sys.argv", ["jbot_cli.py", "-d", str(tmp_path), "task", "add", "task1"]
    ):
        with patch("jbot_tasks.add_task", return_value=False):
            jbot_cli.main()

    with patch(
        "sys.argv", ["jbot_cli.py", "-d", str(tmp_path), "task", "update", "task1"]
    ):
        with patch("jbot_tasks.update_task", return_value=False):
            jbot_cli.main()

    with patch(
        "sys.argv", ["jbot_cli.py", "-d", str(tmp_path), "task", "done", "task1"]
    ):
        with patch("jbot_tasks.complete_task", return_value=False):
            jbot_cli.main()


def test_cli_main_no_args(tmp_path, capsys):
    with patch("sys.argv", ["jbot_cli.py", "-d", str(tmp_path)]):
        jbot_cli.main()
        captured = capsys.readouterr()
        assert "usage" in captured.out


def test_cli_main_misc_commands(tmp_path, capsys):
    with patch("jbot_cli.get_logs") as mock_logs:
        with patch("sys.argv", ["jbot_cli.py", "-d", str(tmp_path), "logs"]):
            jbot_cli.main()
            mock_logs.assert_called_once()

    with patch("jbot_cli.get_messages") as mock_msgs:
        with patch("sys.argv", ["jbot_cli.py", "-d", str(tmp_path), "messages"]):
            jbot_cli.main()
            mock_msgs.assert_called_once()

    with patch("jbot_infra.send_message", return_value=False) as mock_send:
        with patch(
            "sys.argv",
            [
                "jbot_cli.py",
                "-d",
                str(tmp_path),
                "send-message",
                "-f",
                "agent",
                "-m",
                "msg",
            ],
        ):
            jbot_cli.main()
            mock_send.assert_called_once()

    with patch(
        "jbot_infra.get_recent_logs",
        return_value=[{"agent": "mock", "content": {"summary": "NB Logs"}}],
    ):
        jbot_cli.get_logs(str(tmp_path))
        captured = capsys.readouterr()
        assert "NB Logs" in captured.out


def test_cli_main_name_main(tmp_path):
    with patch("jbot_cli.main"):
        with patch.object(jbot_cli, "__name__", "__main__"):
            pass


def test_cli_main_task_errors(tmp_path, capsys):
    with patch("sys.argv", ["jbot_cli.py", "-d", str(tmp_path), "task"]):
        jbot_cli.main()
        captured = capsys.readouterr()
        assert "usage" in captured.out
    version_file = tmp_path / "VERSION"
    version_file.write_text("1.0.0")

    # Show version
    with patch("sys.argv", ["jbot_cli.py", "-d", str(tmp_path), "version", "show"]):
        jbot_cli.main()
    captured = capsys.readouterr()
    assert "Current JBot Version: v1.0.0" in captured.out

    # Bump version
    with patch(
        "sys.argv", ["jbot_cli.py", "-d", str(tmp_path), "version", "bump", "minor"]
    ):
        jbot_cli.main()
    captured = capsys.readouterr()
    assert "Successfully bumped version to: v1.1.0" in captured.out
    assert version_file.read_text() == "1.1.0"

    # Bump error
    with patch("jbot_core.bump_version", return_value=None):
        with patch(
            "sys.argv", ["jbot_cli.py", "-d", str(tmp_path), "version", "bump", "patch"]
        ):
            jbot_cli.main()
        captured = capsys.readouterr()
        assert "Error: Failed to bump version." in captured.out

    # Tag version (mocking subprocess.run)
    with patch("subprocess.run") as mock_run:
        with patch("sys.argv", ["jbot_cli.py", "-d", str(tmp_path), "version", "tag"]):
            jbot_cli.main()
        mock_run.assert_called_once()
        assert "v1.1.0" in mock_run.call_args[0][0]
        captured = capsys.readouterr()
        assert "Creating git tag: v1.1.0" in captured.out

    # Tag error
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, "git tag")
        with patch("sys.argv", ["jbot_cli.py", "-d", str(tmp_path), "version", "tag"]):
            jbot_cli.main()
        captured = capsys.readouterr()
        assert "Error: Git tag failed" in captured.out


def test_cli_version_release(tmp_path, capsys):
    version_file = tmp_path / "VERSION"
    version_file.write_text("1.1.0")
    (tmp_path / ".project_goal").write_text("Vision")

    # Happy path
    with patch("subprocess.run") as mock_run:
        with patch(
            "sys.argv",
            ["jbot_cli.py", "-d", str(tmp_path), "version", "release", "patch"],
        ):
            jbot_cli.main()

        assert mock_run.call_count == 4
        assert version_file.read_text() == "1.1.1"
        captured = capsys.readouterr()
        assert "Successfully released v1.1.1" in captured.out

    # Dirty workspace
    with patch("jbot_core.is_git_clean", return_value=False):
        with patch(
            "sys.argv",
            ["jbot_cli.py", "-d", str(tmp_path), "version", "release", "patch"],
        ):
            jbot_cli.main()
        captured = capsys.readouterr()
        assert "Error: Git workspace is not clean." in captured.out

    # Bump failure
    with patch("jbot_core.is_git_clean", return_value=True):
        with patch("jbot_core.bump_version", return_value=None):
            with patch(
                "sys.argv",
                ["jbot_cli.py", "-d", str(tmp_path), "version", "release", "minor"],
            ):
                jbot_cli.main()
            captured = capsys.readouterr()
            assert "Error: Failed to bump version." in captured.out
    # Missing part
    with patch("sys.argv", ["jbot_cli.py", "-d", str(tmp_path), "version", "release"]):
        # This will actually fail at argparse level because 'part' is required for 'release'
        # Wait, let's check jbot_cli.py.
        # release_parser.add_argument("part", choices=["major", "minor", "patch"], help="Version part to bump")
        # So argparse handles it.
        # But handle_version also has a check: if not part: print("Error: Must specify version part...")
        # This might be reachable if called directly or if argparse was different.
        pass

    # Let's call handle_version directly for coverage
    jbot_cli.handle_version(str(tmp_path), "release", part=None)
    captured = capsys.readouterr()
    assert "Error: Must specify version part" in captured.out

    # Git failure
    with patch("jbot_core.is_git_clean", return_value=True):
        with patch("subprocess.run") as mock_run:

            def mock_run_side_effect(cmd, *args, **kwargs):
                if "add" in cmd:
                    raise subprocess.CalledProcessError(1, "git add")
                return MagicMock(returncode=0)

            mock_run.side_effect = mock_run_side_effect

            with patch(
                "sys.argv",
                ["jbot_cli.py", "-d", str(tmp_path), "version", "release", "major"],
            ):
                jbot_cli.main()
            captured = capsys.readouterr()
            assert "Error: Release failed during git operations" in captured.out


def test_cli_infrastructure_commands(tmp_path, capsys):
    (tmp_path / ".project_goal").write_text("Vision")

    with (
        patch("jbot_infra.send_message", return_value=True),
        patch("jbot_infra.run_maintenance"),
        patch("jbot_rotation.purge_directives", return_value=5),
        patch("jbot_rotation.rotate_memory", return_value=True),
        patch("jbot_rotation.rotate_tasks", return_value=True),
        patch("jbot_rotation.rotate_messages", return_value=True),
        patch("jbot_infra.generate_dashboard", return_value=True),
    ):
        # send-message
        with patch(
            "sys.argv",
            [
                "jbot_cli.py",
                "-d",
                str(tmp_path),
                "send-message",
                "-f",
                "ceo",
                "-m",
                "hello",
            ],
        ):
            jbot_cli.main()
        assert "Message sent successfully." in capsys.readouterr().out

        # maintenance
        with patch("sys.argv", ["jbot_cli.py", "-d", str(tmp_path), "maintenance"]):
            jbot_cli.main()

        # purge
        with patch("sys.argv", ["jbot_cli.py", "-d", str(tmp_path), "purge"]):
            jbot_cli.main()
        assert "Purged 5 expired directives." in capsys.readouterr().out

        # rotate memory
        with patch(
            "sys.argv", ["jbot_cli.py", "-d", str(tmp_path), "rotate", "memory"]
        ):
            jbot_cli.main()
        assert "Memory log rotated." in capsys.readouterr().out

        # rotate tasks
        with patch("sys.argv", ["jbot_cli.py", "-d", str(tmp_path), "rotate", "tasks"]):
            jbot_cli.main()
        assert "Tasks rotated." in capsys.readouterr().out

        # rotate messages
        with patch(
            "sys.argv", ["jbot_cli.py", "-d", str(tmp_path), "rotate", "messages"]
        ):
            jbot_cli.main()
        assert "Messages rotated." in capsys.readouterr().out

        # dashboard
        with patch("sys.argv", ["jbot_cli.py", "-d", str(tmp_path), "dashboard"]):
            jbot_cli.main()
        assert "Dashboard regenerated." in capsys.readouterr().out


def test_cli_agent_command(tmp_path, capsys):
    with patch("jbot_agent.run_agent") as mock_run_agent:
        with patch(
            "sys.argv",
            [
                "jbot_cli.py",
                "-d",
                str(tmp_path),
                "agent",
                "--name",
                "test-agent",
                "--role",
                "Tester",
            ],
        ):
            jbot_cli.main()

        mock_run_agent.assert_called_once_with(
            name="test-agent",
            role="Tester",
            description=None,
            project_dir=str(tmp_path),
            prompt_file=None,
            gemini_pkg=None,
        )
