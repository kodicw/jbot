import os
import json
import sys
from datetime import datetime
from unittest.mock import patch, MagicMock

# Ensure scripts directory is in sys.path
sys.path.append(os.path.join(os.getcwd(), "scripts"))
import jbot_infra as infra


def test_get_team_registry(tmp_path):
    jbot_dir = tmp_path / ".jbot"
    jbot_dir.mkdir()
    agents_file = jbot_dir / "agents.json"
    data = {"agent1": {"role": "Tester"}}
    agents_file.write_text(json.dumps(data))
    assert infra.get_team_registry(str(tmp_path)) == data


def test_get_recent_messages(tmp_path):
    msgs_dir = tmp_path / "messages"
    msgs_dir.mkdir()
    (msgs_dir / "2026-04-20_12-00-00_ceo.txt").write_text("MSG 1")
    assert len(infra.get_recent_messages(str(msgs_dir), count=5)) == 1
    assert infra.get_recent_messages("nonexistent_dir") == []


def test_get_recent_logs(tmp_path):
    log_file = tmp_path / "memory.log"
    log_file.write_text(
        json.dumps({"agent": "a1", "content": {"summary": "s1"}}) + "\n"
    )
    with open(log_file, "a") as f:
        f.write(json.dumps({"agent": "a2", "content": {"summary": "s2"}}) + "\n")
    logs = infra.get_recent_logs(str(log_file), count=1)
    assert len(logs) == 1 and logs[0]["agent"] == "a2"
    assert infra.get_recent_logs("nonexistent.log") == []


def test_parse_directives(tmp_path):
    dir_path = tmp_path / "directives"
    dir_path.mkdir()
    today = datetime.now().strftime("%Y-%m-%d")
    (dir_path / f"999_{today}_future.txt").write_text("Future")
    (dir_path / "001_2000-01-01_expired.txt").write_text("Expired")
    (dir_path / "002_active.txt").write_text("Active\nExpiration: 2099-01-01")
    directives = infra.parse_directives(str(dir_path))
    filenames = [d["filename"] for d in directives]
    assert f"999_{today}_future.txt" in filenames
    assert "001_2000-01-01_expired.txt" not in filenames
    assert "002_active.txt" in filenames


def test_generate_dashboard(tmp_path):
    (tmp_path / ".project_goal").write_text("Vision")
    (tmp_path / "TASKS.md").write_text("## Active Tasks\n- [ ] Task")
    infra.generate_dashboard("INDEX.md", str(tmp_path))
    assert "Vision" in (tmp_path / "INDEX.md").read_text()


def test_send_message(tmp_path):
    success = infra.send_message(str(tmp_path), "ceo", "hello", subject="Greetings")
    assert success is True
    outbox_dir = tmp_path / ".jbot" / "outbox"
    assert outbox_dir.exists()
    msg_files = os.listdir(outbox_dir)
    assert len(msg_files) == 1 and "ceo.txt" in msg_files[0]


@patch("jbot_infra.NbClient")
def test_run_maintenance(mock_nb_client, tmp_path):
    jbot_dir = tmp_path / ".jbot"
    jbot_dir.mkdir()
    queues_dir = jbot_dir / "queues"
    queues_dir.mkdir()
    (queues_dir / "tester.json").write_text(json.dumps({"summary": "done"}))
    (tmp_path / "TASKS.md").write_text(
        "## Active Tasks\n- [ ] Task\n## Completed Tasks\n- [x] T1"
    )
    assert infra.run_maintenance(str(tmp_path)) is True
    assert (jbot_dir / "memory.log").exists()
    assert not (queues_dir / "tester.json").exists()
    mock_nb_client.assert_called_once()
    mock_nb_client.return_value.add.assert_called_once()


@patch("jbot_infra.NbClient")
def test_get_note_content(mock_nb):
    mock_client = MagicMock()
    mock_nb.return_value = mock_client

    mock_note = MagicMock()
    mock_note.id = "1"
    mock_client.query.return_value = [mock_note]
    mock_client.show.return_value = "Content"

    assert infra.get_note_content("type:tasks") == "Content"
    mock_client.query.assert_called_with("#tasks")
    mock_client.show.assert_called_with("1")

    # Fallback to title search
    mock_client.query.side_effect = [[], [mock_note]]
    assert infra.get_note_content("type:prompt") == "Content"

    # Exception handling
    mock_client.query.side_effect = Exception("Error")
    assert infra.get_note_content("type:idea") is None


@patch("jbot_infra.NbClient")
def test_get_recent_logs_nb(mock_nb):
    mock_client = MagicMock()
    mock_nb.return_value = mock_client

    mock_note = MagicMock()
    mock_note.title = "Memory: [test_agent] - Test Summary"
    mock_client.ls.return_value = [mock_note]

    logs = infra.get_recent_logs()
    assert len(logs) == 1
    assert logs[0]["agent"] == "test_agent"

    mock_client.ls.side_effect = Exception("Error")
    assert infra.get_recent_logs() == []


def test_get_recent_messages_exception(tmp_path):
    msgs_dir = tmp_path / "messages"
    msgs_dir.mkdir()
    f = msgs_dir / "bad.txt"
    f.mkdir()  # directory instead of file to trigger read error
    assert infra.get_recent_messages(str(msgs_dir)) == []


def test_get_recent_logs_exception(tmp_path):
    log_file = tmp_path / "bad.log"
    log_file.write_text("not json")
    assert infra.get_recent_logs(str(log_file)) == []

    # test read permission error by making it a directory
    bad_log = tmp_path / "dir.log"
    bad_log.mkdir()
    assert infra.get_recent_logs(str(bad_log)) == []


def test_parse_directives_exception(tmp_path):
    assert infra.parse_directives("nonexistent") == []
    dir_path = tmp_path / "dirs"
    dir_path.mkdir()
    f = dir_path / "bad.txt"
    f.mkdir()  # trigger read error
    assert infra.parse_directives(str(dir_path)) == []


def test_generate_dashboard_advanced(tmp_path):
    (tmp_path / ".jbot").mkdir()
    (tmp_path / ".jbot/agents.json").write_text(
        '{"agent1": {"role": "dev", "description": "desc"}}'
    )
    (tmp_path / "CHANGELOG.md").write_text("- **Milestone 1**\n- **Milestone 2**")
    infra.generate_dashboard("INDEX.md", str(tmp_path))
    content = (tmp_path / "INDEX.md").read_text()
    assert "agent1" in content
    assert "**Milestones Achieved:** 2" in content
    assert "- **Milestone 1**" in content


def test_consolidate_messages_errors(tmp_path):
    assert infra.consolidate_messages(str(tmp_path)) is None  # no outbox
    (tmp_path / ".jbot/outbox").mkdir(parents=True)
    (tmp_path / ".jbot/outbox/msg.txt").write_text("hi")
    # trigger error by not having messages dir
    infra.consolidate_messages(str(tmp_path))


def test_consolidate_memory_errors(tmp_path):
    assert infra.consolidate_memory(str(tmp_path)) is None  # no queues
    queues = tmp_path / ".jbot/queues"
    queues.mkdir(parents=True)
    f = queues / "agent.json"
    f.write_text('{"summary": "test"}')
    # trigger error by bad nb client
    with patch("jbot_infra.NbClient") as mock_nb:
        mock_nb.return_value.add.side_effect = Exception("err")
        infra.consolidate_memory(str(tmp_path))
        assert f.exists()  # Should not have been removed due to error


@patch("jbot_infra.initialize_infrastructure", side_effect=Exception("Crash"))
def test_run_maintenance_error(mock_init, tmp_path):
    assert infra.run_maintenance(str(tmp_path)) is False


@patch("jbot_infra.NbClient")
def test_get_note_content_no_id(mock_nb):
    mock_client = MagicMock()
    mock_nb.return_value = mock_client
    mock_client.query.return_value = []
    assert infra.get_note_content("type:missing") is None


def test_parse_directives_filename_expired(tmp_path):
    dir_path = tmp_path / "directives2"
    dir_path.mkdir()
    (dir_path / "001_2000-01-01_expired.txt").write_text("No content exp")
    assert infra.parse_directives(str(dir_path)) == []


def test_consolidate_messages_success(tmp_path):
    (tmp_path / ".jbot/outbox").mkdir(parents=True)
    (tmp_path / ".jbot/messages").mkdir(parents=True)
    (tmp_path / ".jbot/outbox/msg.txt").write_text("hi")
    infra.consolidate_messages(str(tmp_path))
    assert not (tmp_path / ".jbot/outbox/msg.txt").exists()
    assert (tmp_path / ".jbot/messages/msg.txt").exists()


def test_get_recent_messages_permission_error(tmp_path):
    msgs_dir = tmp_path / "messages_perm"
    msgs_dir.mkdir()
    f = msgs_dir / "bad.txt"
    f.write_text("ok")
    # we need to simulate open() failing on a valid file.
    # We can mock builtins.open
    with patch("builtins.open", side_effect=PermissionError("denied")):
        assert infra.get_recent_messages(str(msgs_dir)) == []
