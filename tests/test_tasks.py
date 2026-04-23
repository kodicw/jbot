import os
import sys
from unittest.mock import patch, MagicMock

# Ensure scripts directory is in sys.path
sys.path.append(os.path.join(os.getcwd(), "scripts"))
import jbot_tasks as tasks


def test_parse_tasks(tmp_path):
    with patch(
        "jbot_infra.get_note_content",
        return_value="\n## Strategic Vision\nGoal: Excellence.\n\n## Active Tasks\n- [ ] **Task 1** (Agent: test)\n- [ ] **Task 2**\n\n## Backlog\n- [ ] **Backlog 1**\n\n## Completed Tasks\n- [x] **Task 3**\n",
    ):
        data = tasks.parse_tasks()
        assert data["vision"] == "Goal: Excellence."
        assert "- [ ] **Task 1** (Agent: test)" in data["active"]
        assert "- [ ] **Backlog 1**" in data["backlog"]
        assert data["done_count"] == 1

    with patch("jbot_infra.get_note_content", return_value=""):
        assert tasks.parse_tasks()["active"] == []


def test_add_task():
    with patch(
        "jbot_infra.get_note_content", return_value="## Strategic Vision\nGoal\n"
    ):
        with patch("jbot_tasks._push_nb_tasks", return_value=True) as mock_push:
            tasks.add_task("New Task")
            assert "- [ ] **New Task**" in mock_push.call_args[0][0]

            tasks.add_task("Second Task", agent="lead")
            assert "- [ ] **Second Task** (Agent: lead)" in mock_push.call_args[0][0]

            tasks.add_task("Backlog Task", backlog=True)
            assert "## Backlog" in mock_push.call_args[0][0]
            assert "- [ ] **Backlog Task**" in mock_push.call_args[0][0]


def test_update_task():
    with patch(
        "jbot_infra.get_note_content",
        return_value="\n## Active Tasks\n- [ ] **Old Task** (Agent: lead)\n## Backlog\n- [ ] **Wait Task**\n",
    ):
        with patch("jbot_tasks._push_nb_tasks", return_value=True) as mock_push:
            tasks.update_task("Old Task", new_text="Updated Task", agent="tester")
            assert "- [ ] **Updated Task** (Agent: tester)" in mock_push.call_args[0][0]

            tasks.update_task("Wait Task", move_to="active")
            assert "## Active Tasks" in mock_push.call_args[0][0]

            assert tasks.update_task("NonExistentTask") is False


def test_complete_task():
    with patch(
        "jbot_infra.get_note_content",
        return_value="\n## Active Tasks\n- [ ] **Working Task**\n## Completed Tasks\n",
    ):
        with patch("jbot_tasks._push_nb_tasks", return_value=True) as mock_push:
            tasks.complete_task("Working Task")
            assert "- [x] **Working Task**" in mock_push.call_args[0][0]

    with patch("jbot_infra.get_note_content", return_value=""):
        assert tasks.complete_task("Task") is False


@patch("jbot_infra.NbClient")
def test_push_nb_tasks(mock_nb):
    mock_client = MagicMock()
    mock_nb.return_value = mock_client

    assert tasks._push_nb_tasks("Content") is True
    mock_client.add.assert_called_once_with(
        title="Task Board", content="Content", tags=["type:tasks"], overwrite=True
    )

    mock_client.add.side_effect = Exception("Error")
    assert tasks._push_nb_tasks("Content") is False


@patch("jbot_infra.get_note_content")
def test_parse_tasks_nb(mock_get_note):
    mock_get_note.return_value = "## Strategic Vision\nNb Goal"
    data = tasks.parse_tasks()
    assert data["vision"] == "Nb Goal"


@patch("jbot_infra.get_note_content")
@patch("jbot_tasks._push_nb_tasks", return_value=True)
def test_add_task_nb(mock_push, mock_get_note):
    mock_get_note.return_value = "## Active Tasks\n"
    assert tasks.add_task("Nb Task") is True
    mock_push.assert_called_once()
    assert "- [ ] **Nb Task**" in mock_push.call_args[0][0]


@patch("jbot_infra.get_note_content")
@patch("jbot_tasks._push_nb_tasks", return_value=True)
def test_update_task_nb(mock_push, mock_get_note):
    mock_get_note.return_value = (
        "## Active Tasks\n- [ ] Unbolded Task\n- [ ] **Target Task** (Agent: foo)"
    )
    assert tasks.update_task("Unbolded Task", "Bolded Task") is True
    assert "- [ ] **Bolded Task**" in mock_push.call_args[0][0]

    # Test move_to header missing fallback
    mock_get_note.return_value = "## Active Tasks\n- [ ] **Move Me**"
    assert tasks.update_task("Move Me", move_to="backlog") is True
    assert "## Backlog" in mock_push.call_args[0][0]


@patch("jbot_infra.get_note_content")
@patch("jbot_tasks._push_nb_tasks", return_value=True)
def test_complete_task_nb(mock_push, mock_get_note):
    mock_get_note.return_value = "## Active Tasks\n- [ ] **Finish Me**\n"
    assert tasks.complete_task("Finish Me") is True
    mock_push.assert_called_once()
    assert "- [x] **Finish Me**" in mock_push.call_args[0][0]
    assert "## Completed Tasks" in mock_push.call_args[0][0]
