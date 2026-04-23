import os
import subprocess
import re
from dataclasses import dataclass
from typing import List, Optional, Dict


@dataclass
class NbNote:
    id: str
    title: str
    tags: List[str]
    content: Optional[str] = None
    filename: Optional[str] = None


class NbClient:
    """
    A standalone Python client for interacting with the `nb` CLI knowledge base.
    This client is designed to be reusable and can be exposed as an MCP server.
    """

    def __init__(self, notebook: str = "jbot", env: Optional[Dict[str, str]] = None):
        self.notebook = notebook
        self.env = env or os.environ.copy()

        # Ensure non-interactive behavior
        if "EDITOR" not in self.env:
            self.env["EDITOR"] = "cat"
        if "PAGER" not in self.env:
            self.env["PAGER"] = "cat"

    def _run(self, args: List[str]) -> subprocess.CompletedProcess:
        """Helper to run nb commands."""
        return subprocess.run(
            ["nb", "--no-color"] + args,
            capture_output=True,
            text=True,
            env=self.env,
        )

    def add(
        self,
        title: str,
        content: str,
        tags: Optional[List[str]] = None,
        overwrite: bool = False,
    ) -> Optional[str]:
        """
        Add a new note to the notebook.
        Returns the ID of the new note or None if it failed.
        """
        args = [f"{self.notebook}:add", "--title", title, "--content", content]
        if tags:
            args.extend(["--tags", ",".join(tags)])
        if overwrite:
            args.extend(["--overwrite", "--force"])

        result = self._run(args)
        if result.returncode == 0 and result.stdout:
            # Output format: Added: [1] 20260422.md "Title"
            # Or: Added: [1] 🔖 bookmark.md
            match = re.search(r"Added:\s*\[(?:[^\]]*:)?(\d+)\]", result.stdout)
            if match:
                return match.group(1)
        return None

    def show(self, note_id: str) -> Optional[str]:
        """
        Get the full content of a note by ID.
        """
        result = self._run([f"{self.notebook}:show", note_id, "--print"])
        if result.returncode == 0:
            return result.stdout.strip()
        return None

    def query(self, query: str) -> List[NbNote]:
        """
        Search notes in the notebook using nb <notebook>:q
        Returns a list of NbNote objects.
        """
        result = self._run([f"{self.notebook}:q", query])
        if result.returncode != 0:
            return []

        return self._parse_ls_output(result.stdout)

    def ls(
        self, tags: Optional[List[str]] = None, limit: Optional[int] = None
    ) -> List[NbNote]:
        """
        List notes in the notebook, optionally filtered by tags.
        """
        args = [f"{self.notebook}:ls"]
        if tags:
            args.extend(["--tags", ",".join(tags)])
        if limit is not None:
            args.extend(["--limit", str(limit)])

        result = self._run(args)
        if result.returncode != 0:
            return []

        return self._parse_ls_output(result.stdout)

    def _parse_ls_output(self, output: str) -> List[NbNote]:
        """
        Parse the output of nb ls or nb q into NbNote objects.
        Expected format: [jbot:123] Title of the note
        Or: [123] Title of the note
        """
        notes = []
        for line in output.strip().splitlines():
            line = line.strip()
            if not line or line.startswith("-"):
                continue

            # Regex to match [id], [notebook:id], or [notebook/path:id] followed by the title
            match = re.search(r"\[(?:[^\]]*:)?(\d+)\]\s+(.*)", line)
            if match:
                note_id = match.group(1)
                title = match.group(2).strip()
                # Remove emoji indicators if present (🔖, 🔒, etc.)
                title = re.sub(r"^[🔖🔒📂🌄📄📹🔉📖✔️✅📌]\s*", "", title)
                notes.append(NbNote(id=note_id, title=title, tags=[]))
        return notes
