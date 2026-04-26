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

        # Ensure non-interactive behavior and avoid missing 'less' issues
        self.env["EDITOR"] = "cat"
        self.env["PAGER"] = "cat"
        self.env["NB_PAGER"] = "cat"

        # Mock 'less' if missing to prevent nb from crashing on _less_prompt
        # Create a temp bin if needed or just use /bin/true as less
        tmp_bin = "/tmp/jbot_bin"
        os.makedirs(tmp_bin, exist_ok=True)
        less_path = os.path.join(tmp_bin, "less")
        if not os.path.exists(less_path):
            with open(less_path, "w") as f:
                f.write(
                    '#!/bin/sh\nif [ "$1" = "--version" ]; then echo "less 1"; else cat "$@"; fi\n'
                )
            os.chmod(less_path, 0o755)

        if tmp_bin not in self.env.get("PATH", ""):
            self.env["PATH"] = f"{tmp_bin}:{self.env.get('PATH', '')}"

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
        # Use --names-only or similar if available, but nb q doesn't seem to have it.
        # However, we can use nb ls with a query string in some versions,
        # but nb q is the standard search.
        result = self._run([f"{self.notebook}:q", query])
        if result.returncode != 0:
            return []

        return self._parse_ls_output(result.stdout)

    def edit(
        self,
        note_id: str,
        content: Optional[str] = None,
        title: Optional[str] = None,
        tags: Optional[List[str]] = None,
        overwrite: bool = True,
    ) -> bool:
        """
        Update an existing note's content, title, or tags.
        """
        args = [f"{self.notebook}:edit", note_id]
        if content is not None:
            args.extend(["--content", content])
        if title is not None:
            args.extend(["--title", title])
        if tags is not None:
            args.extend(["--tags", ",".join(tags)])
        if overwrite:
            args.append("--overwrite")

        result = self._run(args)
        return result.returncode == 0

    def ls(
        self, tags: Optional[List[str]] = None, limit: Optional[int] = None
    ) -> List[NbNote]:
        """
        List notes in the notebook, optionally filtered by tags.
        """
        args = [f"{self.notebook}:ls", "-a"]
        if tags:
            for tag in tags:
                # Use #tag syntax for reliable tag filtering in nb queries
                clean_tag = tag.lstrip("#")
                args.append(f"#{clean_tag}")

        if limit is not None:
            args.append(f"--{limit}")

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

    def delete(self, note_id: str) -> bool:
        """
        Delete a note by ID.
        """
        result = self._run([f"{self.notebook}:delete", note_id, "--force"])
        return result.returncode == 0
