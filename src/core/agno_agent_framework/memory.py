"""
Agent Memory Management

Manages agent memory, including short-term and long-term memory storage.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
import json


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
        max_long_term: int = 1000
    ):
        """
        Initialize agent memory.
        
        Args:
            agent_id: Agent identifier
            max_short_term: Maximum short-term memory items
            max_long_term: Maximum long-term memory items
        """
        self.agent_id = agent_id
        self.max_short_term = max_short_term
        self.max_long_term = max_long_term
        
        self._short_term: List[MemoryItem] = []
        self._long_term: Dict[str, MemoryItem] = {}
        self._episodic: List[MemoryItem] = []
        self._semantic: Dict[str, MemoryItem] = {}
    
    def store(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.SHORT_TERM,
        importance: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
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
            tags=tags or []
        )
        
        if memory_type == MemoryType.SHORT_TERM:
            self._short_term.append(memory)
            # Trim if exceeds max
            if len(self._short_term) > self.max_short_term:
                # Remove least important items
                self._short_term.sort(key=lambda m: m.importance)
                self._short_term = self._short_term[-self.max_short_term:]
        
        elif memory_type == MemoryType.LONG_TERM:
            self._long_term[memory.memory_id] = memory
            # Trim if exceeds max
            if len(self._long_term) > self.max_long_term:
                # Remove least important items
                sorted_items = sorted(
                    self._long_term.values(),
                    key=lambda m: m.importance
                )
                to_remove = sorted_items[:len(sorted_items) - self.max_long_term]
                for item in to_remove:
                    self._long_term.pop(item.memory_id, None)
        
        elif memory_type == MemoryType.EPISODIC:
            self._episodic.append(memory)
        
        elif memory_type == MemoryType.SEMANTIC:
            self._semantic[memory.memory_id] = memory
        
        return memory
    
    def retrieve(
        self,
        query: Optional[str] = None,
        memory_type: Optional[MemoryType] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10
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
        results = []
        
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
                m for m in memories_to_search
                if any(tag in m.tags for tag in tags)
            ]
        
        # Simple text search if query provided
        if query:
            query_lower = query.lower()
            memories_to_search = [
                m for m in memories_to_search
                if query_lower in m.content.lower()
            ]
        
        # Sort by importance and recency
        memories_to_search.sort(
            key=lambda m: (m.importance, m.last_accessed),
            reverse=True
        )
        
        # Update access counts
        for memory in memories_to_search[:limit]:
            memory.access_count += 1
            memory.last_accessed = datetime.now()
        
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
            return True
        
        # Try episodic
        for i, memory in enumerate(self._episodic):
            if memory.memory_id == memory_id:
                self._episodic.pop(i)
                return True
        
        # Try semantic
        if memory_id in self._semantic:
            self._semantic.pop(memory_id)
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
        important = [
            m for m in self._short_term
            if m.importance >= 0.7
        ]
        
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
                timestamp=memory.timestamp
            )
            
            self._long_term[long_term_memory.memory_id] = long_term_memory
            self._short_term.remove(memory)
            consolidated += 1
        
        return consolidated
    
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
                len(self._short_term) +
                len(self._long_term) +
                len(self._episodic) +
                len(self._semantic)
            )
        }

