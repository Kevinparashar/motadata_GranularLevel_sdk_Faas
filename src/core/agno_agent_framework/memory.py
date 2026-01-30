"""
Agent Memory Management

Manages agent memory, including short-term and long-term memory storage.
"""

import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .exceptions import MemoryPersistenceError, MemoryWriteError


class MemoryType(str, Enum):
    """Memory type enumeration."""

    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"


class MemoryItem(BaseModel):
    """Individual memory item."""

    memory_id: str
    agent_id: str
    memory_type: MemoryType
    content: str
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.now)
    access_count: int = 0
    last_accessed: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)


class AgentMemory:
    """
    Agent memory system for storing and retrieving information.

    Manages both short-term (working) memory and long-term
    (persistent) memory for agents.
    """

    def __init__(
        self,
        agent_id: str,
        max_short_term: int = 50,
        max_long_term: int = 1000,
        max_episodic: int = 500,  # Limit for episodic memory (ITSM ticket history)
        max_semantic: int = 2000,  # Limit for semantic memory (knowledge patterns)
        max_age_days: Optional[int] = 30,  # Optional max age for automatic cleanup
        persistence_path: Optional[str] = None,
    ):
        """
        Initialize agent memory.

        Args:
            agent_id: Agent identifier
            max_short_term: Maximum short-term memory items
            max_long_term: Maximum long-term memory items
            max_episodic: Maximum episodic memory items (default: 500 for ITSM)
            max_semantic: Maximum semantic memory items (default: 2000 for ITSM)
            max_age_days: Optional maximum age in days for automatic cleanup
            persistence_path: Optional path for memory persistence
        """
        self.agent_id = agent_id
        self.max_short_term = max_short_term
        self.max_long_term = max_long_term
        self.max_episodic = max_episodic
        self.max_semantic = max_semantic
        self.max_age_days = max_age_days
        self._persistence_path = Path(persistence_path) if persistence_path else None

        self._short_term: List[MemoryItem] = []
        self._long_term: Dict[str, MemoryItem] = {}
        self._episodic: List[MemoryItem] = []
        self._semantic: Dict[str, MemoryItem] = {}

        if self._persistence_path and self._persistence_path.exists():
            try:
                self._load()
            except (OSError, IOError, ValueError, KeyError) as e:
                # If load fails, continue with empty memory
                # Log the error for debugging but don't fail initialization
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(
                    f"Failed to load memory from {self._persistence_path}: {e}. "
                    "Continuing with empty memory.",
                    exc_info=True
                )

    def _trim_short_term(self, memory: MemoryItem) -> None:
        """Trim short-term memory if exceeds max limit."""
        self._short_term.append(memory)
        if len(self._short_term) > self.max_short_term:
            # Remove least important items (LRU-like eviction based on importance)
            self._short_term.sort(key=lambda m: m.importance)
            self._short_term = self._short_term[-self.max_short_term :]

    def _trim_long_term(self, memory: MemoryItem) -> None:
        """Trim long-term memory if exceeds max limit."""
        self._long_term[memory.memory_id] = memory
        if len(self._long_term) > self.max_long_term:
            # Remove least important items
            sorted_items = sorted(self._long_term.values(), key=lambda m: m.importance)
            to_remove = sorted_items[: len(sorted_items) - self.max_long_term]
            for item in to_remove:
                self._long_term.pop(item.memory_id, None)

    def _trim_episodic(self, memory: MemoryItem) -> None:
        """Trim episodic memory if exceeds max limit."""
        self._episodic.append(memory)
        if len(self._episodic) > self.max_episodic:
            # FIFO - remove oldest
            self._episodic = self._episodic[-self.max_episodic :]

    def _trim_semantic(self, memory: MemoryItem) -> None:
        """Trim semantic memory if exceeds max limit."""
        self._semantic[memory.memory_id] = memory
        if len(self._semantic) > self.max_semantic:
            sorted_items = sorted(self._semantic.values(), key=lambda m: m.importance)
            to_remove = sorted_items[: len(sorted_items) - self.max_semantic]
            for item in to_remove:
                self._semantic.pop(item.memory_id, None)

    def store(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.SHORT_TERM,
        importance: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ) -> MemoryItem:
        """
        Store a memory item.

        Args:
            content: Memory content
            memory_type: Type of memory
            importance: Importance score (0.0-1.0)
            metadata: Optional metadata
            tags: Optional tags

        Returns:
            Created memory item
        """
        import uuid

        memory = MemoryItem(
            memory_id=str(uuid.uuid4()),
            agent_id=self.agent_id,
            memory_type=memory_type,
            content=content,
            importance=importance,
            metadata=metadata or {},
            tags=tags or [],
        )

        # BOUNDED MEMORY: Enforce memory limits to prevent unbounded growth
        # This ensures memory usage stays within configured limits, preventing memory leaks
        # and controlling token usage in prompts (more memory = more tokens = higher cost)
        if memory_type == MemoryType.SHORT_TERM:
            self._trim_short_term(memory)
        elif memory_type == MemoryType.LONG_TERM:
            self._trim_long_term(memory)
        elif memory_type == MemoryType.EPISODIC:
            # EPISODIC MEMORY: Stores conversation episodes (query-answer pairs)
            # Used by RAG system to provide conversation context
            # FIFO eviction: oldest episodes removed first (maintains recent conversation history)
            self._trim_episodic(memory)
        elif memory_type == MemoryType.SEMANTIC:
            self._trim_semantic(memory)

        try:
            self._persist()
        except Exception as e:
            raise MemoryWriteError(
                message=f"Failed to persist memory: {str(e)}",
                agent_id=self.agent_id,
                memory_id=memory.memory_id,
                memory_type=(
                    memory_type.value if hasattr(memory_type, "value") else str(memory_type)
                ),
                operation="store",
                original_error=e,
            )
        return memory

    def retrieve(
        self,
        query: Optional[str] = None,
        memory_type: Optional[MemoryType] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10,
    ) -> List[MemoryItem]:
        """
        Retrieve memory items.

        Args:
            query: Optional search query
            memory_type: Optional memory type filter
            tags: Optional tag filter
            limit: Maximum number of results

        Returns:
            List of memory items
        """
        # Determine which memories to search
        memories_to_search = []

        if memory_type is None or memory_type == MemoryType.SHORT_TERM:
            memories_to_search.extend(self._short_term)

        if memory_type is None or memory_type == MemoryType.LONG_TERM:
            memories_to_search.extend(self._long_term.values())

        if memory_type is None or memory_type == MemoryType.EPISODIC:
            memories_to_search.extend(self._episodic)

        if memory_type is None or memory_type == MemoryType.SEMANTIC:
            memories_to_search.extend(self._semantic.values())

        # Filter by tags if provided
        if tags:
            memories_to_search = [
                m for m in memories_to_search if any(tag in m.tags for tag in tags)
            ]

        # Simple text search if query provided
        if query:
            query_lower = query.lower()
            memories_to_search = [m for m in memories_to_search if query_lower in m.content.lower()]

        # Sort by importance and recency
        memories_to_search.sort(key=lambda m: (m.importance, m.last_accessed), reverse=True)

        # Update access counts
        for memory in memories_to_search[:limit]:
            memory.access_count += 1
            memory.last_accessed = datetime.now()

        self._persist()
        return memories_to_search[:limit]

    def forget(self, memory_id: str) -> bool:
        """
        Forget a memory item.

        Args:
            memory_id: Memory identifier

        Returns:
            True if memory was found and removed
        """
        # Try short-term
        for i, memory in enumerate(self._short_term):
            if memory.memory_id == memory_id:
                self._short_term.pop(i)
                return True

        # Try long-term
        if memory_id in self._long_term:
            self._long_term.pop(memory_id)
            self._persist()
            return True

        # Try episodic
        for i, memory in enumerate(self._episodic):
            if memory.memory_id == memory_id:
                self._episodic.pop(i)
                return True

        # Try semantic
        if memory_id in self._semantic:
            self._semantic.pop(memory_id)
            self._persist()
            return True

        return False

    def consolidate(self) -> int:
        """
        Consolidate short-term memories to long-term.

        Moves important short-term memories to long-term storage.

        Returns:
            Number of memories consolidated
        """
        # Find important short-term memories
        important = [m for m in self._short_term if m.importance >= 0.7]

        consolidated = 0
        for memory in important:
            # Create long-term version
            long_term_memory = MemoryItem(
                memory_id=memory.memory_id,
                agent_id=memory.agent_id,
                memory_type=MemoryType.LONG_TERM,
                content=memory.content,
                importance=memory.importance,
                metadata=memory.metadata,
                tags=memory.tags,
                timestamp=memory.timestamp,
            )

            self._long_term[long_term_memory.memory_id] = long_term_memory
            self._short_term.remove(memory)
            consolidated += 1
        self._persist()

        return consolidated

    def cleanup_expired(self, max_age_days: Optional[int] = None) -> int:
        """
        Remove memories older than specified days.

        Args:
            max_age_days: Maximum age in days (uses instance default if None)

        Returns:
            Number of memories removed
        """
        from datetime import timedelta

        max_age = max_age_days or self.max_age_days
        if max_age is None:
            return 0

        cutoff = datetime.now() - timedelta(days=max_age)
        removed = 0

        # Clean short-term
        before = len(self._short_term)
        self._short_term = [m for m in self._short_term if m.timestamp > cutoff]
        removed += before - len(self._short_term)

        # Clean long-term
        to_remove = [mid for mid, m in self._long_term.items() if m.timestamp <= cutoff]
        for mid in to_remove:
            self._long_term.pop(mid, None)
            removed += 1

        # Clean episodic
        before = len(self._episodic)
        self._episodic = [m for m in self._episodic if m.timestamp > cutoff]
        removed += before - len(self._episodic)

        # Clean semantic
        to_remove = [mid for mid, m in self._semantic.items() if m.timestamp <= cutoff]
        for mid in to_remove:
            self._semantic.pop(mid, None)
            removed += 1

        if removed > 0:
            self._persist()

        return removed

    def check_memory_pressure(self) -> Dict[str, Any]:
        """
        Check if memory usage is high.

        Returns:
            Dictionary with memory pressure information
        """
        total = (
            len(self._short_term) + len(self._long_term) + len(self._episodic) + len(self._semantic)
        )

        max_total = self.max_short_term + self.max_long_term + self.max_episodic + self.max_semantic

        usage_ratio = total / max_total if max_total > 0 else 0

        return {
            "total_memories": total,
            "max_total": max_total,
            "usage_ratio": usage_ratio,
            "under_pressure": usage_ratio > 0.8,
            "breakdown": {
                "short_term": {
                    "count": len(self._short_term),
                    "max": self.max_short_term,
                    "usage": (
                        len(self._short_term) / self.max_short_term
                        if self.max_short_term > 0
                        else 0
                    ),
                },
                "long_term": {
                    "count": len(self._long_term),
                    "max": self.max_long_term,
                    "usage": (
                        len(self._long_term) / self.max_long_term if self.max_long_term > 0 else 0
                    ),
                },
                "episodic": {
                    "count": len(self._episodic),
                    "max": self.max_episodic,
                    "usage": (
                        len(self._episodic) / self.max_episodic if self.max_episodic > 0 else 0
                    ),
                },
                "semantic": {
                    "count": len(self._semantic),
                    "max": self.max_semantic,
                    "usage": (
                        len(self._semantic) / self.max_semantic if self.max_semantic > 0 else 0
                    ),
                },
            },
        }

    def handle_memory_pressure(self) -> int:
        """
        Automatically clean up when under memory pressure.

        MEMORY PRESSURE HANDLING:
        - Triggered when memory usage > 80% of limits
        - First: Remove expired memories (older than max_age_days)
        - Then: Remove least important memories (bottom 10%)
        - This prevents memory from growing unbounded and keeps token usage controlled

        Returns:
            Number of memories removed
        """
        pressure = self.check_memory_pressure()

        if not pressure["under_pressure"]:
            return 0

        # STEP 1: Clean up old memories first (age-based eviction)
        # This removes memories that are past their expiration date
        removed = self.cleanup_expired(max_age_days=7)

        # STEP 2: If still under pressure, remove least important memories
        # This is importance-based eviction: keeps important memories, removes less important ones
        if self.check_memory_pressure()["under_pressure"]:
            # Collect all memories from all types
            all_memories = (
                list(self._short_term)
                + list(self._long_term.values())
                + list(self._episodic)
                + list(self._semantic.values())
            )
            # Sort by importance (lowest first) and access count (least accessed first)
            all_memories.sort(key=lambda m: (m.importance, m.access_count))

            # Remove bottom 10% (least important and least accessed)
            to_remove = all_memories[: max(1, len(all_memories) // 10)]
            for memory in to_remove:
                self.forget(memory.memory_id)
                removed += 1

        return removed

    def get_stats(self) -> Dict[str, Any]:
        """
        Get memory statistics.

        Returns:
            Dictionary with memory statistics
        """
        return {
            "agent_id": self.agent_id,
            "short_term_count": len(self._short_term),
            "long_term_count": len(self._long_term),
            "episodic_count": len(self._episodic),
            "semantic_count": len(self._semantic),
            "total_count": (
                len(self._short_term)
                + len(self._long_term)
                + len(self._episodic)
                + len(self._semantic)
            ),
            "limits": {
                "max_short_term": self.max_short_term,
                "max_long_term": self.max_long_term,
                "max_episodic": self.max_episodic,
                "max_semantic": self.max_semantic,
            },
            "pressure": self.check_memory_pressure(),
        }

    def _persist(self) -> None:
        """Persist memory to disk if configured."""
        if not self._persistence_path:
            return
        try:
            data = {
                "short_term": [m.model_dump() for m in self._short_term],
                "long_term": [m.model_dump() for m in self._long_term.values()],
                "episodic": [m.model_dump() for m in self._episodic],
                "semantic": [m.model_dump() for m in self._semantic.values()],
            }
            self._persistence_path.parent.mkdir(parents=True, exist_ok=True)
            with self._persistence_path.open("w", encoding="utf-8") as f:
                json.dump(data, f, default=str)
        except Exception as e:
            raise MemoryPersistenceError(
                message=f"Failed to persist memory to disk: {str(e)}",
                agent_id=self.agent_id,
                file_path=str(self._persistence_path) if self._persistence_path else None,
                operation="save",
                original_error=e,
            )

    def _load(self) -> None:
        if not self._persistence_path or not self._persistence_path.exists():
            return
        try:
            with self._persistence_path.open("r", encoding="utf-8") as f:
                data = json.load(f)

            def _parse(items: List[Dict[str, Any]]) -> List[MemoryItem]:
                parsed: List[MemoryItem] = []
                for item in items:
                    parsed.append(MemoryItem(**item))
                return parsed

            self._short_term = _parse(data.get("short_term", []))
            self._long_term = {m.memory_id: m for m in _parse(data.get("long_term", []))}
            self._episodic = _parse(data.get("episodic", []))
            self._semantic = {m.memory_id: m for m in _parse(data.get("semantic", []))}
        except Exception as e:
            raise MemoryPersistenceError(
                message=f"Failed to load memory from disk: {str(e)}",
                agent_id=self.agent_id,
                file_path=str(self._persistence_path) if self._persistence_path else None,
                operation="load",
                original_error=e,
            )
