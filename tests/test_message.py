import os
import pytest
from unittest.mock import patch
import sys
import importlib

# Ensure scripts directory is in sys.path
sys.path.append(os.path.join(os.getcwd(), "scripts"))
jbot_message = importlib.import_module("jbot-message")

def test_send_message(tmp_path):
    project_dir = tmp_path
    msgs_dir = project_dir / ".jbot" / "messages"
    msgs_dir.mkdir(parents=True)
    
    jbot_message.send_message(str(project_dir), "sender", "Hello world", "Greetings")
    
    msg_files = [f for f in os.listdir(msgs_dir) if f.endswith(".txt")]
    assert len(msg_files) == 1
    content = (msgs_dir / msg_files[0]).read_text()
    assert "From: sender" in content
    assert "Subject: Greetings" in content
    assert "Hello world" in content

def test_message_main(tmp_path):
    project_dir = tmp_path
    msgs_dir = project_dir / ".jbot" / "messages"
    msgs_dir.mkdir(parents=True)
    
    with patch("sys.argv", ["jbot-message.py", "-d", str(project_dir), "-f", "tester", "-s", "Hello", "-m", "Body"]):
        jbot_message.main()
    
    msg_files = [f for f in os.listdir(msgs_dir) if f.endswith(".txt")]
    assert len(msg_files) == 1
    content = (msgs_dir / msg_files[0]).read_text()
    assert "From: tester" in content
    assert "Subject: Hello" in content
    assert "Body" in content
