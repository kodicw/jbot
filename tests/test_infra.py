import os
import json
import sys
from datetime import datetime
from unittest.mock import patch, MagicMock

# Ensure scripts directory is in sys.path
sys.path.insert(0, os.path.join(os.getcwd(), "scripts"))
import jbot_infra as infra
import jbot_utils as utils


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


@patch("jbot_infra.get_memory_client")
def test_get_recent_logs(mock_nb):
    mock_client = MagicMock()
    mock_nb.return_value = mock_client

    mock_note1 = MagicMock()
    mock_note1.title = "Memory: [a1] - s1"
    mock_note2 = MagicMock()
    mock_note2.title = "Memory: [a2] - s2"
    mock_client.ls.return_value = [mock_note1, mock_note2]

    logs = infra.get_recent_logs(count=1)
    assert len(logs) == 2
    assert logs[1]["agent"] == "a2"


@patch("jbot_infra.get_memory_client")
def test_get_recent_logs_exception(mock_nb):
    mock_client = MagicMock()
    mock_nb.return_value = mock_client
    mock_client.ls.side_effect = Exception("err")
    assert infra.get_recent_logs() == []


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
    # Dashboard uses jbot_tasks.parse_tasks now, so we might need to mock it if we want full isolation,
    # but for now we'll just let it run.
    utils.generate_dashboard("INDEX.md", str(tmp_path))
    assert "Vision" in (tmp_path / "INDEX.md").read_text()


def test_send_message(tmp_path):
    success = infra.send_message(str(tmp_path), "ceo", "hello", subject="Greetings")
    assert success is True
    outbox_dir = tmp_path / ".jbot" / "outbox"
    assert outbox_dir.exists()
    msg_files = os.listdir(outbox_dir)
    assert len(msg_files) == 1 and "ceo.txt" in msg_files[0]


@patch("jbot_infra.get_memory_client")
def test_run_maintenance(mock_nb_client, tmp_path):
    jbot_dir = tmp_path / ".jbot"
    jbot_dir.mkdir()
    queues_dir = jbot_dir / "queues"
    queues_dir.mkdir()
    (queues_dir / "tester.json").write_text(json.dumps({"summary": "done"}))
    infra.run_maintenance(str(tmp_path))
    assert not (queues_dir / "tester.json").exists()
    mock_nb_client.return_value.add.assert_called_once()


@patch("jbot_infra.get_memory_client")
def test_get_note_content(mock_nb):
    mock_client = MagicMock()
    mock_nb.return_value = mock_client

    mock_note = MagicMock()
    mock_note.id = "1"
    mock_client.ls.return_value = [mock_note]
    mock_client.show.return_value = "Content"

    # Tag search
    assert infra.get_note_content("type:tasks") == "Content"
    mock_client.ls.assert_called_with(tags=["tasks"])
    mock_client.show.assert_called_with("1")

    # Fallback to query
    mock_client.ls.return_value = []
    mock_client.query.return_value = [mock_note]
    assert infra.get_note_content("some query") == "Content"
    mock_client.query.assert_called_with("some query")

    # Fallback to title search for prompt
    # Note: query is called twice, first with type:prompt, then with Authoritative System Prompt
    mock_client.query.side_effect = [[], [mock_note]]
    assert infra.get_note_content("type:prompt") == "Content"

    # Exception handling
    mock_client.ls.side_effect = Exception("Error")
    assert infra.get_note_content("type:idea") is None


@patch("jbot_infra.get_memory_client")
def test_get_note_content_no_id(mock_nb):
    mock_client = MagicMock()
    mock_nb.return_value = mock_client
    mock_client.ls.return_value = []
    mock_client.query.return_value = []
    assert infra.get_note_content("type:missing") is None


def test_get_recent_messages_exception(tmp_path):
    msgs_dir = tmp_path / "messages"
    msgs_dir.mkdir()
    f = msgs_dir / "bad.txt"
    f.mkdir()  # directory instead of file to trigger read error
    assert infra.get_recent_messages(str(msgs_dir)) == []


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
    utils.generate_dashboard("INDEX.md", str(tmp_path))
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
    with patch("jbot_infra.get_memory_client") as mock_nb:
        mock_nb.return_value.add.side_effect = Exception("err")
        infra.consolidate_memory(str(tmp_path))
        assert f.exists()  # Should not have been removed due to error


@patch("jbot_infra.initialize_infrastructure", side_effect=Exception("Crash"))
def test_run_maintenance_error(mock_init, tmp_path):
    assert infra.run_maintenance(str(tmp_path)) is False


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
    with patch("builtins.open", side_effect=PermissionError("denied")):
        assert infra.get_recent_messages(str(msgs_dir)) == []
