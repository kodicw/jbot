import os
import subprocess
import sys
from abc import ABC, abstractmethod
from typing import Optional, List
import jbot_core as core

class AiInterface(ABC):
    """Abstract base class for AI CLI interfaces."""
    
    def __init__(self, binary_path: str):
        self.binary_path = binary_path

    @abstractmethod
    def get_command(self, prompt: str) -> List[str]:
        """Returns the command list to execute the AI CLI."""
        pass

    def run(self, prompt: str, agent_name: str) -> int:
        """Executes the AI CLI and streams output."""
        cmd = self.get_command(prompt)
        core.log(f"Invoking AI CLI: {' '.join(cmd)}", agent_name)
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            for line in process.stdout:
                print(line, end="", flush=True)
            process.wait()
            return process.returncode
        except Exception as e:
            core.log(f"Error executing AI CLI: {e}", agent_name)
            return 1

class GeminiInterface(AiInterface):
    """Interface for the Gemini CLI."""
    
    def get_command(self, prompt: str) -> List[str]:
        # -y: assume yes, -p: prompt
        return [self.binary_path, "-y", "-p", prompt]

class OpenCodeInterface(AiInterface):
    """Interface for the OpenCode CLI."""
    
    def get_command(self, prompt: str) -> List[str]:
        # run: execute command, [message]: positional prompt
        # --dangerously-skip-permissions: auto-approve for autonomous execution
        return [self.binary_path, "run", prompt, "--dangerously-skip-permissions"]

def get_interface(name: str, binary_path: str) -> AiInterface:
    """Factory function to get the appropriate AI interface."""
    if "opencode" in binary_path.lower() or name.lower() == "opencode":
        return OpenCodeInterface(binary_path)
    return GeminiInterface(binary_path)
