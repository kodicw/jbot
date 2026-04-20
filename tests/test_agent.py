import os
import json
import pytest
from unittest.mock import patch, MagicMock
from scripts.jbot_agent import get_tree, get_goal, get_rag_entries, get_team_registry, get_messages, get_directives

# Note: We need to handle the import correctly depending on how pytest is run.
# For simplicity in this environment, I'll mock the import if needed or just use sys.path.
import sys
sys.path.append(os.path.join(os.getcwd(), "scripts"))
import importlib
jbot_agent = importlib.import_module("jbot-agent")

def test_get_goal(tmp_path):
    goal_file = tmp_path / ".project_goal"
    goal_file.write_text("Test Goal")
    assert jbot_agent.get_goal(str(goal_file)) == "Test Goal"

def test_get_goal_missing():
    assert jbot_agent.get_goal("/non/existent/path") == "Maintain and improve the JBot project infrastructure."

def test_get_rag_entries(tmp_path):
    memory_log = tmp_path / "memory.log"
    memory_log.write_text(json.dumps({"agent": "test", "content": {"summary": "Summary 1"}}) + "\n")
    memory_log.write_text(json.dumps({"agent": "test", "content": {"summary": "Summary 2"}}) + "\n", mode="a")
    
    rag = jbot_agent.get_rag_entries(str(memory_log))
    assert "[test] Summary 1" in rag
    assert "[test] Summary 2" in rag

def test_get_team_registry(tmp_path):
    agents_json = tmp_path / "agents.json"
    agents_json.write_text(json.dumps({
        "agent1": {"role": "Role 1", "description": "Desc 1"},
        "agent2": {"role": "Role 2", "description": "Desc 2"}
    }))
    
    registry = jbot_agent.get_team_registry(str(agents_json), "agent1")
    assert "agent2: Role 2 (Desc 2)" in registry
    assert "agent1" not in registry

def test_get_messages(tmp_path):
    messages_dir = tmp_path / "messages"
    messages_dir.mkdir()
    (messages_dir / "2026-04-20_12-00-00_test.txt").write_text("Hello")
    
    messages = jbot_agent.get_messages(str(messages_dir), "other")
    assert "--- Message 2026-04-20_12-00-00_test.txt ---" in messages
    assert "Hello" in messages

def test_get_directives(tmp_path):
    directives_dir = tmp_path / "directives"
    directives_dir.mkdir()
    (directives_dir / "001_directive.txt").write_text("Directive 1")
    
    directives = jbot_agent.get_directives(str(directives_dir))
    assert "Directive 1" in directives
