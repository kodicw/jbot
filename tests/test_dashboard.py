import os
import json
import sys
import importlib

# Ensure scripts directory is in sys.path
sys.path.append(os.path.join(os.getcwd(), "scripts"))
jbot_dashboard = importlib.import_module("jbot-dashboard")


def test_generate_dashboard(tmp_path):
    # Setup mock project
    (tmp_path / ".project_goal").write_text("Test Goal")
    (tmp_path / "TASKS.md").write_text("## Active Tasks\n- [ ] Task 1\n- [x] Done Task")
    (tmp_path / "CHANGELOG.md").write_text("- **Milestone 1**\n- **Milestone 2**")

    jbot_dir = tmp_path / ".jbot"
    jbot_dir.mkdir()
    (jbot_dir / "agents.json").write_text(
        json.dumps({"agent1": {"role": "Tester", "description": "Desc"}})
    )

    output_file = tmp_path / "DASHBOARD.md"
    jbot_dashboard.generate_dashboard(str(output_file), str(tmp_path))

    content = output_file.read_text()
    assert "# JBot PAO Dashboard" in content
    assert "Test Goal" in content
    assert "agent1" in content
    assert "Task 1" in content
    assert "Milestone 1" in content
