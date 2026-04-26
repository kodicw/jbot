import os
import sys
from unittest.mock import patch, MagicMock

# Ensure scripts directory is in sys.path
sys.path.insert(0, os.path.join(os.getcwd(), "scripts"))
import jbot_tasks as tasks


def test_parse_tasks():
    # Mock vision note
    with patch(
        "jbot_infra.get_note_content",
        return_value="## Strategic Vision\n> Autonomous AI engineering.",
    ):
        # Mock granular tasks
        mock_tasks = [
            {
                "id": "1",
                "title": "Task 1",
                "content": "Status: status:active\nAgent: lead",
                "status": "active",
                "agent": "lead",
            },
            {
                "id": "2",
                "title": "Task 2",
                "content": "Status: status:backlog",
                "status": "backlog",
                "agent": None,
            },
            {
                "id": "3",
                "title": "Task 3",
                "content": "Status: status:completed",
                "status": "completed",
                "agent": "tester",
            },
        ]
        with patch("jbot_tasks._get_granular_tasks", return_value=mock_tasks):
            data = tasks.parse_tasks()
            assert data["vision"] == "Autonomous AI engineering."
            assert "- [ ] **Task 1** (Agent: lead)" in data["active"]
            assert "- [ ] **Task 2**" in data["backlog"]
            assert data["done_count"] == 1
            assert "- [x] **Task 3** (Agent: tester)" in "".join(
                data["sections"]["completed"]
            )


def test_get_granular_tasks():
    with patch("jbot_infra.NbClient") as mock_nb_class:
        mock_client = MagicMock()
        mock_nb_class.return_value = mock_client

        # Mock ls results
        mock_client.ls.return_value = [
            MagicMock(id="10", title="Real Task"),
            MagicMock(id="11", title="ADR: Something"),
        ]

        # Mock show results
        def mock_show(note_id):
            if note_id == "10":
                return "Status: status:active\nAgent: lead\nDescription: Real Task"
            return None

        mock_client.show.side_effect = mock_show

        tasks_list = tasks._get_granular_tasks()
        assert len(tasks_list) == 1
        assert tasks_list[0]["id"] == "10"
        assert tasks_list[0]["status"] == "active"
        assert tasks_list[0]["agent"] == "lead"


def test_add_task():
    with patch("jbot_infra.NbClient") as mock_nb_class:
        mock_client = MagicMock()
        mock_nb_class.return_value = mock_client
        mock_client.add.return_value = "100"

        assert tasks.add_task("New Task", agent="lead") is True
        mock_client.add.assert_called_once()
        args, kwargs = mock_client.add.call_args
        assert kwargs["title"] == "New Task"
        assert "status:active" in kwargs["content"]
        assert "agent:lead" in kwargs["tags"]


def test_update_task():
    mock_tasks = [
        {
            "id": "1",
            "title": "Old Task",
            "content": "Status: status:active\nAgent: lead",
            "status": "active",
            "agent": "lead",
        }
    ]
    with patch("jbot_tasks._get_granular_tasks", return_value=mock_tasks):
        with patch("jbot_infra.NbClient") as mock_nb_class:
            mock_client = MagicMock()
            mock_nb_class.return_value = mock_client
            mock_client.edit.return_value = True

            assert tasks.update_task("Old Task", new_text="New Task", move_to="backlog")
            mock_client.edit.assert_called_once()
            args, kwargs = mock_client.edit.call_args
            assert args[0] == "1"
            assert "status:backlog" in kwargs["content"]
            assert kwargs["title"] == "New Task"


def test_complete_task():
    mock_tasks = [
        {
            "id": "1",
            "title": "Task to Finish",
            "content": "Status: status:active\nAgent: lead",
            "status": "active",
            "agent": "lead",
        }
    ]
    with patch("jbot_tasks._get_granular_tasks", return_value=mock_tasks):
        with patch("jbot_infra.NbClient") as mock_nb_class:
            mock_client = MagicMock()
            mock_nb_class.return_value = mock_client
            mock_client.edit.return_value = True

            assert tasks.complete_task("Finish")
            mock_client.edit.assert_called_once()
            args, kwargs = mock_client.edit.call_args
            assert "status:completed" in kwargs["content"]
            assert "status:completed" in kwargs["tags"]


def test_parse_tasks_fallback():
    # Test fallback to old task board if granular tasks are empty
    with patch("jbot_tasks._get_granular_tasks", return_value=[]):
        with patch(
            "jbot_infra.get_note_content",
            side_effect=[
                None,  # Vision
                "## Active Tasks\n- [ ] **Old Task**\n",  # Tasks
            ],
        ):
            data = tasks.parse_tasks()
            assert "- [ ] **Old Task**" in data["active"]
