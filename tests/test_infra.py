import os
import json
import sys
from datetime import datetime
from unittest.mock import patch

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
