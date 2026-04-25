import os
import sys
import pytest
from unittest.mock import patch

# Ensure scripts directory is in sys.path
sys.path.append(os.path.join(os.getcwd(), "scripts"))
import jbot_tasks as tasks

# Context: [[nb:jbot:adr-193]] - Robust Section Parsing Verification

ROBUST_CONTENT = """# Authoritative Task Board (CEO)

#tasks #type:tasks

## 🎯 Strategic Vision
**Autonomous, Multi-Agent Engineering on NixOS.**

## 🚀 ACTIVE TASKS
- [ ] Task 1
- [x] Task 2 (done)

## 📦 Backlog Highlights
- [ ] Task 3

## ✅ Completed Tasks
- [x] Task 4
"""

@patch('jbot_tasks._get_nb_tasks')
def test_robust_section_parsing(mock_get_tasks):
    mock_get_tasks.return_value = ROBUST_CONTENT
    
    data = tasks.parse_tasks()
    
    # Check vision extraction (case-insensitive, handles icons)
    assert "Autonomous, Multi-Agent Engineering on NixOS." in data["vision"]
    
    # Check active tasks (case-insensitive: ACTIVE TASKS)
    assert len(data["active"]) == 1
    assert "Task 1" in data["active"][0]
    
    # Check backlog (case-insensitive)
    assert len(data["backlog"]) == 1
    assert "Task 3" in data["backlog"][0]
    
    # Check done count (Task 2 in active + Task 4 in completed)
    assert data["done_count"] == 2

@patch('jbot_tasks._get_nb_tasks')
def test_header_aliases_parsing(mock_get_tasks):
    content = """## Goal
- Reach for the stars

## Done
- [x] Task 10
"""
    mock_get_tasks.return_value = content
    data = tasks.parse_tasks()
    
    assert "Reach for the stars" in data["vision"]
    assert data["done_count"] == 1

if __name__ == "__main__":
    pytest.main([__file__])
