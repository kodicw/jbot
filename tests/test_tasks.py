import os
import sys

# Ensure scripts directory is in sys.path
sys.path.append(os.path.join(os.getcwd(), "scripts"))
import jbot_tasks as tasks


def test_parse_tasks(tmp_path):
    tasks_file = tmp_path / "TASKS.md"
    tasks_file.write_text(
        "\n## Strategic Vision\nGoal: Excellence.\n\n## Active Tasks\n- [ ] **Task 1** (Agent: test)\n- [ ] **Task 2**\n\n## Backlog\n- [ ] **Backlog 1**\n\n## Completed Tasks\n- [x] **Task 3**\n"
    )
    data = tasks.parse_tasks(str(tasks_file))
    assert data["vision"] == "Goal: Excellence."
    assert "- [ ] **Task 1** (Agent: test)" in data["active"]
    assert "- [ ] **Backlog 1**" in data["backlog"]
    assert data["done_count"] == 1
    assert tasks.parse_tasks("nonexistent.md")["active"] == []


def test_add_task(tmp_path):
    tasks_file = tmp_path / "TASKS.md"
    tasks_file.write_text("## Strategic Vision\nGoal\n")
    tasks.add_task(str(tasks_file), "New Task")
    assert "- [ ] **New Task**" in tasks_file.read_text()
    tasks.add_task(str(tasks_file), "Second Task", agent="lead")
    assert "- [ ] **Second Task** (Agent: lead)" in tasks_file.read_text()
    tasks.add_task(str(tasks_file), "Backlog Task", backlog=True)
    assert (
        "## Backlog" in tasks_file.read_text()
        and "- [ ] **Backlog Task**" in tasks_file.read_text()
    )


def test_update_task(tmp_path):
    tasks_file = tmp_path / "TASKS.md"
    tasks_file.write_text(
        "\n## Active Tasks\n- [ ] **Old Task** (Agent: lead)\n## Backlog\n- [ ] **Wait Task**\n"
    )
    tasks.update_task(
        str(tasks_file), "Old Task", new_text="Updated Task", agent="tester"
    )
    assert "- [ ] **Updated Task** (Agent: tester)" in tasks_file.read_text()
    tasks.update_task(str(tasks_file), "Updated Task", move_to="backlog")
    data = tasks.parse_tasks(str(tasks_file))
    assert any("Updated Task" in t for t in data["backlog"])
    tasks.update_task(str(tasks_file), "Wait Task", move_to="active")
    assert any("Wait Task" in t for t in tasks.parse_tasks(str(tasks_file))["active"])
    assert tasks.update_task("nonexistent.md", "Task") is False
    assert tasks.update_task(str(tasks_file), "NonExistentTask") is False


def test_complete_task(tmp_path):
    tasks_file = tmp_path / "TASKS.md"
    tasks_file.write_text(
        "\n## Active Tasks\n- [ ] **Working Task**\n## Completed Tasks\n"
    )
    tasks.complete_task(str(tasks_file), "Working Task")
    assert "- [x] **Working Task**" in tasks_file.read_text()
    assert tasks.complete_task("nonexistent.md", "Task") is False
