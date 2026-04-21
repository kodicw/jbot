import os
import json
from unittest.mock import patch, MagicMock
import sys
import importlib
import pytest
import subprocess

# Ensure scripts directory is in sys.path
sys.path.append(os.path.join(os.getcwd(), "scripts"))
jbot_agent = importlib.import_module("jbot-agent")


@pytest.fixture
def agent_env(tmp_path):
    project_dir = tmp_path
    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text("Hello {AGENT_NAME}, {PROJECT_GOAL}")

    (project_dir / ".project_goal").write_text("Maintain JBot")
    (project_dir / "TASKS.md").write_text("## Active Tasks\n")

    jbot_dir = project_dir / ".jbot"
    jbot_dir.mkdir()
    (jbot_dir / "agents.json").write_text(
        json.dumps({"dev": {"role": "Lead", "description": "Dev"}})
    )
    (jbot_dir / "queues").mkdir()
    (jbot_dir / "messages").mkdir()
    (jbot_dir / "directives").mkdir()

    env = {
        "AGENT_NAME": "dev",
        "AGENT_ROLE": "Lead",
        "AGENT_DESCRIPTION": "Dev",
        "PROJECT_DIR": str(project_dir),
        "PROMPT_FILE": str(prompt_file),
        "GEMINI_PACKAGE": "echo",
    }
    with patch.dict(os.environ, env):
        yield tmp_path


def test_agent_main(agent_env):
    tmp_path = agent_env
    # Mock Popen and run
    with patch("subprocess.Popen") as mock_popen, patch("subprocess.run"):
        mock_process = MagicMock()
        mock_process.stdout = ["Success response\n"]
        mock_process.wait.return_value = 0
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        jbot_agent.main()

        assert mock_popen.called
        args, kwargs = mock_popen.call_args
        prompt_arg = args[0][4]
        assert "Hello dev, Maintain JBot" in prompt_arg


def test_agent_missing_env():
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(SystemExit) as e:
            jbot_agent.main()
        assert e.value.code == 1


def test_agent_with_rag_and_human(agent_env):
    tmp_path = agent_env
    jbot_dir = tmp_path / ".jbot"
    
    # Add memory logs
    with open(jbot_dir / "memory.log", "w") as f:
        f.write(json.dumps({"agent": "ceo", "content": {"summary": "Vision set"}}) + "\n")
        f.write(json.dumps({"agent": "lead", "content": {"summary": "Code done"}}) + "\n")
    
    # Add human input
    (jbot_dir / "messages" / "human.txt").write_text("Focus on tests")
    
    # Add messages
    (jbot_dir / "messages" / "msg1.txt").write_text("Hello team")

    # Add directives
    (jbot_dir / "directives" / "dir1.txt").write_text("Strict standards")

    with patch("subprocess.Popen") as mock_popen, patch("subprocess.run"):
        mock_process = MagicMock()
        mock_process.stdout = ["Success\n"]
        mock_process.wait.return_value = 0
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        jbot_agent.main()

        args, _ = mock_popen.call_args
        prompt = args[0][4]
        assert "[ceo] Vision set" in prompt
        assert "[lead] Code done" in prompt
        assert "Focus on tests" in prompt
        assert "Hello team" in prompt
        assert "Strict standards" in prompt


def test_agent_gemini_failure(agent_env):
    with patch("subprocess.Popen") as mock_popen:
        mock_process = MagicMock()
        mock_process.stdout = ["Error from gemini\n"]
        mock_process.wait.return_value = 1
        mock_process.returncode = 1
        mock_popen.return_value = mock_process

        with pytest.raises(SystemExit) as e:
            jbot_agent.main()
        assert e.value.code == 1


def test_agent_with_pre_commit_success(agent_env):
    tmp_path = agent_env
    hooks_dir = tmp_path / ".githooks"
    hooks_dir.mkdir()
    pre_commit = hooks_dir / "pre-commit"
    pre_commit.write_text("#!/bin/sh\nexit 0")
    pre_commit.chmod(0o755)

    with patch("subprocess.Popen") as mock_popen, patch("subprocess.run") as mock_run:
        mock_process = MagicMock()
        mock_process.stdout = ["Success\n"]
        mock_process.wait.return_value = 0
        mock_process.returncode = 0
        mock_popen.return_value = mock_process
        
        mock_run.return_value = MagicMock(returncode=0)

        jbot_agent.main()
        
        # Verify pre-commit was called
        # The script calls subprocess.run(["bash", pre_commit_script])
        mock_run.assert_called_with(["bash", str(pre_commit)], check=True)


def test_agent_with_pre_commit_failure(agent_env):
    tmp_path = agent_env
    hooks_dir = tmp_path / ".githooks"
    hooks_dir.mkdir()
    pre_commit = hooks_dir / "pre-commit"
    pre_commit.write_text("#!/bin/sh\nexit 1")
    pre_commit.chmod(0o755)

    with patch("subprocess.Popen") as mock_popen, patch("subprocess.run") as mock_run:
        mock_process = MagicMock()
        mock_process.stdout = ["Success\n"]
        mock_process.wait.return_value = 0
        mock_process.returncode = 0
        mock_popen.return_value = mock_process
        
        mock_run.side_effect = subprocess.CalledProcessError(1, "bash")

        # Failure in pre-commit shouldn't exit with 1 if it's just a warning in the script
        # Wait, let's check jbot-agent.py line 167: utils.log(f"WARNING: Verification failed: {e}", agent_name)
        # It catches Exception and logs warning, but doesn't exit.
        jbot_agent.main()
        assert mock_run.called


def test_agent_git_tree(agent_env):
    tmp_path = agent_env
    (tmp_path / ".git").mkdir()
    
    with patch("subprocess.check_output") as mock_check:
        mock_check.side_effect = ["file1\nfile2\n" + "longfile\n"*60, b"unused"]
        
        with patch("subprocess.Popen") as mock_popen, patch("subprocess.run"):
            mock_process = MagicMock()
            mock_process.stdout = ["Success\n"]
            mock_process.wait.return_value = 0
            mock_process.returncode = 0
            mock_popen.return_value = mock_process

            jbot_agent.main()
            
            args, _ = mock_popen.call_args
            prompt = args[0][4]
            assert "... (truncated)" in prompt

def test_agent_git_tree_error(agent_env):
    tmp_path = agent_env
    (tmp_path / ".git").mkdir()
    
    with patch("subprocess.check_output") as mock_check:
        mock_check.side_effect = Exception("git error")
        
        with patch("subprocess.Popen") as mock_popen, patch("subprocess.run"):
            mock_process = MagicMock()
            mock_process.stdout = ["Success\n"]
            mock_process.wait.return_value = 0
            mock_process.returncode = 0
            mock_popen.return_value = mock_process

            jbot_agent.main()
            
            args, _ = mock_popen.call_args
            prompt = args[0][4]
            assert "Error running git ls-files" in prompt
