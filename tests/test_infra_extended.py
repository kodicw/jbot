import os
import json
import sys
import pytest
from unittest.mock import patch, MagicMock

# Ensure scripts directory is in sys.path
sys.path.insert(0, os.path.join(os.getcwd(), "scripts"))
import jbot_utils as utils


@pytest.fixture
def mock_nb_client():
    with patch("jbot_utils.get_memory_client") as mock:
        client = MagicMock()
        mock.return_value = client
        yield client


def test_generate_dashboard_with_roi(tmp_path, mock_nb_client):
    # Setup project structure
    project_dir = tmp_path
    jbot_dir = project_dir / ".jbot"
    jbot_dir.mkdir()

    # Agents
    agents_file = jbot_dir / "agents.json"
    agents_file.write_text(
        json.dumps({"tester": {"role": "QA", "description": "Verify changes"}})
    )

    # Changelog (Milestones)
    changelog = project_dir / "CHANGELOG.md"
    changelog.write_text("- **Milestone 1**\n- **Milestone 2**")

    # Tasks (Mock jbot_tasks.parse_tasks)
    tasks_data = {
        "active": ["- [ ] Task 1 (Agent: lead)", "- [ ] Task 2"],
        "backlog": ["- [ ] Backlog 1"],
        "done_count": 5,
        "sections": {"completed": ["- [x] Done 1", "- [x] Done 2"]},
    }

    # Mock NbClient for ROI
    mock_nb_client.ls.side_effect = [
        [MagicMock() for _ in range(15)],  # all_notes (Knowledge Base Growth)
        [MagicMock() for _ in range(3)],  # adr_notes (Architectural Density)
    ]

    with patch("jbot_tasks.parse_tasks", return_value=tasks_data):
        with patch(
            "jbot_utils.get_recent_adrs",
            return_value=[{"id": "205", "title": "ADR: ROI"}],
        ):
            # Create a mermaid file to cover mermaid logic
            scripts_dir = project_dir / "scripts"
            scripts_dir.mkdir()
            mermaid_file = scripts_dir / "test.mermaid"
            mermaid_file.write_text("graph TD\nA-->B")

            output_file = project_dir / "INDEX.md"
            utils.generate_dashboard(str(output_file), str(project_dir))

            content = output_file.read_text()

            # Verify ROI Metrics
            assert "### 📊 Technical ROI (Engineering Metrics)" in content
            assert "**Engineering Velocity:** 2.50 tasks/milestone" in content  # 5 / 2
            assert "**Architectural Density:** 1.50 ADRs/milestone" in content  # 3 / 2
            assert "**Knowledge Base Growth:** 15 records" in content
            assert "**Completion Ratio:** 62.5%" in content  # 5 / (2+1+5) = 5/8 = 0.625

            # Verify Agent string parsing in active tasks
            assert "Task 1 [lead]" in content
            assert "Task 2" in content

            # Verify Mermaid diagram
            assert "### Test" in content
            assert "```mermaid" in content
            assert "graph TD" in content


def test_generate_dashboard_roi_exception(tmp_path, mock_nb_client):
    mock_nb_client.ls.side_effect = Exception("NB Error")

    output_file = tmp_path / "INDEX.md"
    # Should not crash but log error
    with patch("jbot_core.log") as mock_log:
        utils.generate_dashboard(str(output_file), str(tmp_path))
        mock_log.assert_called_with(
            "Error calculating Technical ROI: NB Error", "Utils"
        )
        assert "Technical ROI" not in output_file.read_text()
