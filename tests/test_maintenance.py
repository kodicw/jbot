import os
import json
import sys
import importlib
from unittest.mock import patch

# Ensure scripts directory is in sys.path
sys.path.append(os.path.join(os.getcwd(), "scripts"))
jbot_maintenance = importlib.import_module("jbot-maintenance")


def test_maintenance_main(tmp_path):
    # Setup mock environment
    project_dir = tmp_path
    os.environ["PROJECT_DIR"] = str(project_dir)

    queues_dir = project_dir / ".jbot" / "queues"
    queues_dir.mkdir(parents=True)
    memory_log = project_dir / ".jbot" / "memory.log"

    # Create a mock queue file
    q_file = queues_dir / "tester.json"
    q_data = {"summary": "Finished tests", "status": "success"}
    q_file.write_text(json.dumps(q_data))

    # Mock subprocess.run to avoid running real scripts
    with patch("subprocess.run") as mock_run:
        jbot_maintenance.main()

        # Check if memory was consolidated
        assert memory_log.exists()
        log_content = memory_log.read_text()
        assert "tester" in log_content
        assert "Finished tests" in log_content

        # Check if queue file was removed
        assert not q_file.exists()

        # Check if other scripts were called
        # scripts: purge, rotate, rotate-tasks, rotate-messages, dashboard
        assert mock_run.call_count == 5
