import os
import json
import pytest
from unittest.mock import patch, MagicMock
import sys
import importlib

# Ensure scripts directory is in sys.path
sys.path.append(os.path.join(os.getcwd(), "scripts"))
jbot_agent = importlib.import_module("jbot-agent")

def test_agent_main(tmp_path):
    # Setup environment
    project_dir = tmp_path
    prompt_file = tmp_path / "prompt.txt"
    # Note: Use placeholders that match the script
    prompt_file.write_text("Hello {AGENT_NAME}, {PROJECT_GOAL}")
    
    (project_dir / ".project_goal").write_text("Maintain JBot")
    (project_dir / "TASKS.md").write_text("## Active Tasks\n")
    
    jbot_dir = project_dir / ".jbot"
    jbot_dir.mkdir()
    (jbot_dir / "agents.json").write_text(json.dumps({"dev": {"role": "Lead", "description": "Dev"}}))
    
    os.environ["AGENT_NAME"] = "dev"
    os.environ["AGENT_ROLE"] = "Lead"
    os.environ["AGENT_DESCRIPTION"] = "Dev"
    os.environ["PROJECT_DIR"] = str(project_dir)
    os.environ["PROMPT_FILE"] = str(prompt_file)
    os.environ["GEMINI_PACKAGE"] = "echo" # Mock gemini
    
    # Mock Popen and run
    with patch("subprocess.Popen") as mock_popen, patch("subprocess.run") as mock_run:
        # Mock Popen return value
        mock_process = MagicMock()
        mock_process.stdout = ["Success response\n"]
        mock_process.wait.return_value = 0
        mock_process.returncode = 0
        mock_popen.return_value = mock_process
        
        jbot_agent.main()
        
        # Verify Popen was called for Gemini
        assert mock_popen.called
        args, kwargs = mock_popen.call_args
        assert args[0][0] == "echo"
        # Check if the prompt was formatted correctly
        prompt_arg = args[0][4]
        assert "Hello dev, Maintain JBot" in prompt_arg
