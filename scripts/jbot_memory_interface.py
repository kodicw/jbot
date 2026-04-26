from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class MemoryNote:
    id: str
    title: str
    tags: List[str]
    content: Optional[str] = None
    filename: Optional[str] = None


class MemoryInterface(ABC):
    """
    Abstract Base Class for JBot memory backends.
    """

    @abstractmethod
    def add(
        self,
        title: str,
        content: str,
        tags: Optional[List[str]] = None,
        overwrite: bool = False,
    ) -> Optional[str]:
        """Add a new note. Returns ID or None."""
        pass

    @abstractmethod
    def show(self, note_id: str) -> Optional[str]:
        """Get full content of a note by ID."""
        pass

    @abstractmethod
    def query(self, query: str) -> List[MemoryNote]:
        """Search notes. Returns a list of MemoryNote objects."""
        pass

    @abstractmethod
    def edit(
        self,
        note_id: str,
        content: Optional[str] = None,
        title: Optional[str] = None,
        tags: Optional[List[str]] = None,
        overwrite: bool = True,
    ) -> bool:
        """Update an existing note."""
        pass

    @abstractmethod
    def ls(
        self, tags: Optional[List[str]] = None, limit: Optional[int] = None
    ) -> List[MemoryNote]:
        """List notes, optionally filtered by tags."""
        pass

    @abstractmethod
    def delete(self, note_id: str) -> bool:
        """Delete a note by ID."""
        pass


def get_memory_client(backend: str = "nb", **kwargs) -> MemoryInterface:
    """
    Factory function to instantiate the configured memory backend.
    """
    if backend == "nb":
        from nb_client import NbClient

        return NbClient(**kwargs)
    else:
        raise ValueError(f"Unsupported memory backend: {backend}")
