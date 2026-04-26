import os
import sys
from unittest.mock import patch, MagicMock

# Ensure scripts directory is in sys.path
sys.path.insert(0, os.path.join(os.getcwd(), "scripts"))
import jbot_utils as utils
from jbot_memory_interface import MemoryNote


def test_update_note_stably_add():
    with patch("jbot_utils.get_memory_client") as mock_nb:
        mock_client = MagicMock()
        mock_nb.return_value = mock_client
        mock_client.ls.return_value = []
        mock_client.add.return_value = "100"

        assert utils.update_note_stably("Title", "Content", ["tag"]) is True
        mock_client.add.assert_called_with("Title", "Content", tags=["tag"])


def test_update_note_stably_edit():
    with patch("jbot_utils.get_memory_client") as mock_nb:
        mock_client = MagicMock()
        mock_nb.return_value = mock_client
        mock_client.ls.return_value = [
            MemoryNote(id="100", title="Title", tags=["tag"])
        ]
        mock_client.edit.return_value = True

        assert utils.update_note_stably("Title", "Content", ["tag"]) is True
        mock_client.edit.assert_called_with("100", "Content")


def test_update_note_stably_exception():
    with patch("jbot_utils.get_memory_client") as mock_nb:
        mock_client = MagicMock()
        mock_nb.return_value = mock_client
        mock_client.ls.side_effect = Exception("error")
        assert utils.update_note_stably("T", "C", ["t"]) is False


def test_get_directive_expiration():
    assert utils.get_directive_expiration("None") is None
    assert utils.get_directive_expiration("None", "no-date.txt") is None
    assert utils.get_directive_expiration("Expiration: 2026-01-01") == "2026-01-01"
    assert utils.get_directive_expiration("None", "2026-01-01.txt") == "2026-01-01"


def test_is_directive_expired():
    assert utils.is_directive_expired("None") is False


def test_generate_dashboard_goal_fallback(tmp_path):
    (tmp_path / ".project_goal").write_text("Fallback Goal")
    # Mock tasks to have no vision
    with patch(
        "jbot_tasks.parse_tasks",
        return_value={
            "vision": "",
            "active": [],
            "backlog": [],
            "done_count": 0,
            "sections": {"completed": []},
        },
    ):
        with patch("jbot_infra.get_team_registry", return_value={}):
            utils.generate_dashboard("INDEX.md", str(tmp_path))
            content = (tmp_path / "INDEX.md").read_text()
            assert "Fallback Goal" in content


def test_generate_dashboard_messages(tmp_path):
    (tmp_path / ".jbot/messages").mkdir(parents=True)
    (tmp_path / ".jbot/messages/m1.txt").write_text("From: alice\nSubject: hi\n\nbody")
    (tmp_path / ".jbot/messages/m2.txt").write_text("No headers")

    with patch(
        "jbot_tasks.parse_tasks",
        return_value={
            "vision": "V",
            "active": [],
            "backlog": [],
            "done_count": 0,
            "sections": {"completed": []},
        },
    ):
        with patch("jbot_infra.get_team_registry", return_value={}):
            utils.generate_dashboard("INDEX.md", str(tmp_path))
            content = (tmp_path / "INDEX.md").read_text()
            assert "[alice]** hi" in content
            assert "[unknown]** none" in content


def test_generate_dashboard_error(tmp_path):
    with patch("jbot_tasks.parse_tasks", side_effect=Exception("Task Error")):
        with patch("jbot_infra.get_team_registry", return_value={}):
            utils.generate_dashboard("INDEX.md", str(tmp_path))
            content = (tmp_path / "INDEX.md").read_text()
            assert "# JBot Dashboard" in content
