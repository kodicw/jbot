import os
import json
from unittest.mock import patch, MagicMock
import sys
import pytest
import subprocess

# Ensure scripts directory is in sys.path
sys.path.append(os.path.join(os.getcwd(), "scripts"))
import jbot_agent


@pytest.fixture
def agent_env(tmp_path):
    project_dir = tmp_path
    prompt_file = tmp_path / "prompt.txt"
    # Include all placeholders
    prompt_file.write_text(
        "Hello {AGENT_NAME}, {PROJECT_GOAL}. Tree: {DIRECTORY_TREE}. RAG: {RAG_DATABASE_RESULTS}. Human: {HUMAN_INPUT}. Messages: {MESSAGES}. Directives: {DIRECTIVES}."
    )

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
    # Mock Popen and run
    with patch("subprocess.Popen") as mock_popen, patch("subprocess.run") as mock_run:
        # Allow cp and rsync to work, mock others
        def side_effect(cmd, *args, **kwargs):
            if cmd[0] in ["cp", "rsync", "mkdir"]:
                return subprocess.RealPopen(cmd, *args, **kwargs) if hasattr(subprocess, "RealPopen") else MagicMock(returncode=0)
            return MagicMock(returncode=0)
        
        # Actually we should just let them run for real if possible, 
        # but subprocess.run is patched. 
        # Better: only patch what we need.
        mock_run.side_effect = subprocess.run # Default to real run
        
        mock_process = MagicMock()
        mock_process.stdout = ["Success response\n"]
        mock_process.wait.return_value = 0
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        jbot_agent.main()

        assert mock_popen.called
        args, kwargs = mock_popen.call_args
        prompt_arg = args[0][4]
        # It should find .project_goal because we let subprocess.run work for cp
        assert "Hello dev, Maintain JBot" in prompt_arg


def test_agent_missing_env():
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(SystemExit) as e:
            jbot_agent.main()
        assert e.value.code == 1


def test_agent_with_rag_and_human(agent_env):
    tmp_path = agent_env
    jbot_dir = tmp_path / ".jbot"

    # Add human input
    (jbot_dir / "messages" / "human.txt").write_text("Focus on tests")

    # Add messages
    (jbot_dir / "messages" / "msg1.txt").write_text("Hello team")

    # Add directives
    (jbot_dir / "directives" / "dir1.txt").write_text("Strict standards")

    with patch("subprocess.Popen") as mock_popen, patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.run
        
        # Mock nb call in infra.get_recent_logs
        with patch("jbot_infra.get_recent_logs") as mock_logs:
            mock_logs.return_value = [
                {"agent": "ceo", "content": {"summary": "Vision set"}},
                {"agent": "lead", "content": {"summary": "Code done"}}
            ]
            
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
    with (
        patch("subprocess.Popen") as mock_popen,
        patch("subprocess.run") as mock_run,
    ):
        mock_run.side_effect = subprocess.run
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

    with (
        patch("subprocess.Popen") as mock_popen,
        patch("subprocess.run") as mock_run,
    ):
        # We need to be careful: we want real cp/rsync but mock the pre-commit call if needed, 
        # or just let it run since it's a real file.
        mock_run.side_effect = subprocess.run

        mock_process = MagicMock()
        mock_process.stdout = ["Success\n"]
        mock_process.wait.return_value = 0
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        jbot_agent.main()

        # Check if pre-commit was called. 
        # Since we use subprocess.run for everything, we can check mock_run.call_args_list
        # Wait, if we use side_effect = subprocess.run, mock_run still records calls.
        pre_commit_called = any(
            call.args[0] == ["bash", str(pre_commit)] for call in mock_run.call_args_list
        )
        # Note: it might be called in the workspace, so the path will be different.
        pre_commit_called_workspace = any(
            "jbot-workspace-dev/.githooks/pre-commit" in str(call.args[0]) for call in mock_run.call_args_list
        )
        assert pre_commit_called or pre_commit_called_workspace


def test_agent_with_pre_commit_failure(agent_env):
    tmp_path = agent_env
    hooks_dir = tmp_path / ".githooks"
    hooks_dir.mkdir()
    pre_commit = hooks_dir / "pre-commit"
    pre_commit.write_text("#!/bin/sh\nexit 1")
    pre_commit.chmod(0o755)

    with (
        patch("subprocess.Popen") as mock_popen,
        patch("subprocess.run") as mock_run,
    ):
        # Real run except for the pre-commit which we want to fail
        def side_effect(cmd, *args, **kwargs):
            if isinstance(cmd, list) and len(cmd) > 1 and "pre-commit" in cmd[1]:
                raise subprocess.CalledProcessError(1, cmd)
            return subprocess.run(cmd, *args, **kwargs)
        
        mock_run.side_effect = side_effect

        mock_process = MagicMock()
        mock_process.stdout = ["Success\n"]
        mock_process.wait.return_value = 0
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        jbot_agent.main()
        # Should not exit with 1 because verification failure just discards changes in run_agent
        # Wait, let's check run_agent logic.
        # if verified: ... else: core.log("Changes discarded...")
        # So it doesn't sys.exit(1) on verification failure.


def test_agent_git_tree(agent_env):
    tmp_path = agent_env
    # Create a real git repo in tmp_path
    subprocess.run(["git", "init"], cwd=tmp_path, check=True)
    (tmp_path / "file1").write_text("content")
    subprocess.run(["git", "add", "file1"], cwd=tmp_path, check=True)

    with patch("subprocess.Popen") as mock_popen, patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.run
        
        mock_process = MagicMock()
        mock_process.stdout = ["Success\n"]
        mock_process.wait.return_value = 0
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        # We need to mock the 50 lines limit check if we want to test truncation
        # or just provide many files.
        for i in range(60):
            (tmp_path / f"file{i}").write_text("content")
        subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)

        jbot_agent.main()

        args, _ = mock_popen.call_args
        prompt = args[0][4]
        assert "file1" in prompt
        assert "... (truncated)" in prompt


def test_agent_git_tree_error(agent_env):
    tmp_path = agent_env
    subprocess.run(["git", "init"], cwd=tmp_path, check=True)

    with patch("subprocess.check_output") as mock_check:
        mock_check.side_effect = subprocess.CalledProcessError(1, "git ls-files")

        with patch("subprocess.Popen") as mock_popen, patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.run
            mock_process = MagicMock()
            mock_process.stdout = ["Success\n"]
            mock_process.wait.return_value = 0
            mock_process.returncode = 0
            mock_popen.return_value = mock_process

            jbot_agent.main()

            args, _ = mock_popen.call_args
            prompt = args[0][4]
            assert "Error running git ls-files" in prompt
