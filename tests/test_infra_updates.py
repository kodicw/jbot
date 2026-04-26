import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Ensure scripts directory is in sys.path
sys.path.insert(0, os.path.join(os.getcwd(), "scripts"))
import jbot_infra_updates

@patch("subprocess.run")
@patch("jbot_core.get_git_status")
@patch("os.path.exists")
@patch("jbot_infra.send_message")
def test_generate_infra_pr_success(mock_send, mock_exists, mock_status, mock_run, tmp_path):
    # Setup
    mock_status.return_value = "Clean"
    mock_exists.return_value = True # flake.lock exists
    
    # Mock subprocess.run
    # 1. nix flake update
    # 2. git checkout -b
    # 3. git add
    # 4. git commit
    # 5. git checkout -
    
    res_nix = MagicMock()
    res_nix.stdout = ""
    res_nix.stderr = "• Updated input 'nixpkgs':\n    'a' → 'b'"
    
    res_ok = MagicMock()
    res_ok.stdout = "ok"
    
    mock_run.side_effect = [
        res_nix, # update
        res_ok,  # checkout -b
        res_ok,  # add
        res_ok,  # commit
        res_ok   # checkout -
    ]
    
    # Run
    result = jbot_infra_updates.generate_infra_pr(str(tmp_path))
    
    # Assert
    assert result is True
    assert mock_run.call_count == 5
    mock_send.assert_called_once()

@patch("jbot_core.get_git_status")
def test_generate_infra_pr_dirty_git(mock_status, tmp_path):
    mock_status.return_value = "modified: other.py"
    result = jbot_infra_updates.generate_infra_pr(str(tmp_path))
    assert result is False

@patch("subprocess.run")
@patch("jbot_core.get_git_status")
@patch("os.path.exists")
def test_generate_infra_pr_no_updates(mock_exists, mock_status, mock_run, tmp_path):
    mock_status.return_value = "Clean"
    mock_exists.return_value = True
    
    res_nix = MagicMock()
    res_nix.stdout = ""
    res_nix.stderr = "Everything is up to date"
    mock_run.return_value = res_nix
    
    result = jbot_infra_updates.generate_infra_pr(str(tmp_path))
    assert result is True
    assert mock_run.call_count == 1

@patch("os.path.exists")
@patch("jbot_core.get_git_status")
def test_generate_infra_pr_no_lock_file(mock_status, mock_exists, tmp_path):
    mock_status.return_value = "Clean"
    mock_exists.return_value = False # flake.lock missing
    
    # We need to mock get_flake_update_summary too or it will try to run nix
    with patch("jbot_infra_updates.get_flake_update_summary") as mock_summary:
        mock_summary.return_value = "• Updated input"
        result = jbot_infra_updates.generate_infra_pr(str(tmp_path))
        assert result is False

@patch("subprocess.run")
@patch("jbot_core.get_git_status")
@patch("os.path.exists")
def test_generate_infra_pr_branch_failure(mock_exists, mock_status, mock_run, tmp_path):
    mock_status.return_value = "Clean"
    mock_exists.return_value = True
    
    res_nix = MagicMock()
    res_nix.stdout = ""
    res_nix.stderr = "• Updated input 'nixpkgs'"
    
    from subprocess import CalledProcessError
    mock_run.side_effect = [
        res_nix, # update
        CalledProcessError(1, "git checkout -b", stderr="failed") # branch fail
    ]
    
    result = jbot_infra_updates.generate_infra_pr(str(tmp_path))
    assert result is False

@patch("subprocess.run")
@patch("jbot_core.get_git_status")
@patch("os.path.exists")
def test_generate_infra_pr_commit_failure(mock_exists, mock_status, mock_run, tmp_path):
    mock_status.return_value = "Clean"
    mock_exists.return_value = True
    
    res_nix = MagicMock()
    res_nix.stdout = ""
    res_nix.stderr = "• Updated input 'nixpkgs'"
    res_ok = MagicMock()
    res_ok.stdout = "ok"
    res_ok.stderr = ""
    
    from subprocess import CalledProcessError
    mock_run.side_effect = [
        res_nix, # update
        res_ok,  # checkout -b
        res_ok,  # add
        CalledProcessError(1, "git commit", stderr="failed"), # commit fail
        res_ok   # checkout - (fallback)
    ]
    
    result = jbot_infra_updates.generate_infra_pr(str(tmp_path))
    assert result is False

@patch("subprocess.run")
@patch("jbot_core.get_git_status")
@patch("os.path.exists")
def test_generate_infra_pr_add_failure(mock_exists, mock_status, mock_run, tmp_path):
    mock_status.return_value = "Clean"
    mock_exists.return_value = True
    
    res_nix = MagicMock()
    res_nix.stdout = ""
    res_nix.stderr = "• Updated input 'nixpkgs'"
    res_ok = MagicMock()
    res_ok.stdout = "ok"
    res_ok.stderr = ""
    
    from subprocess import CalledProcessError
    mock_run.side_effect = [
        res_nix, # update
        res_ok,  # checkout -b
        CalledProcessError(1, "git add", stderr="failed"), # add fail
        res_ok   # checkout - (fallback)
    ]
    
    result = jbot_infra_updates.generate_infra_pr(str(tmp_path))
    assert result is False

def test_run_command_exception(tmp_path):
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = Exception("Crash")
        res = jbot_infra_updates.run_command(["ls"], str(tmp_path))
        assert res is None

def test_get_flake_update_summary_exception(tmp_path):
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = Exception("Crash")
        res = jbot_infra_updates.get_flake_update_summary(str(tmp_path))
        assert res == ""
