# Memory Management Improvements Needed

## Current State Analysis

### ✅ Well-Managed Components

1. **Cache Mechanism**
   - ✅ Max size limit (default 1024)
   - ✅ LRU eviction
   - ✅ TTL expiration
   - ✅ Memory monitoring available

2. **Prompt Context**
   - ✅ Max tokens limit (default 4000)
   - ✅ Automatic truncation
   - ✅ Safety margin

3. **Agent Short-Term/Long-Term Memory**
   - ✅ Limits enforced
   - ✅ Automatic trimming

### ❌ Critical Issues

1. **Unbounded Episodic/Semantic Memory**
   - No limits on `_episodic` and `_semantic` collections
   - Can grow indefinitely causing memory leaks

2. **No Time-Based Expiration**
   - Memories never expire automatically
   - Old unused data accumulates

3. **No Global Memory Budget**
   - No system-wide memory limits
   - No coordination between components

## Recommended Fixes

### 1. Add Limits to Episodic/Semantic Memory

```python
# In AgentMemory.__init__
def __init__(
    self,
    agent_id: str,
    max_short_term: int = 50,
    max_long_term: int = 1000,
    max_episodic: int = 500,  # NEW
    max_semantic: int = 2000,  # NEW
    persistence_path: Optional[str] = None
):
    # ...
    self.max_episodic = max_episodic
    self.max_semantic = max_semantic

# In store() method
elif memory_type == MemoryType.EPISODIC:
    self._episodic.append(memory)
    # Trim if exceeds max
    if len(self._episodic) > self.max_episodic:
        # Remove oldest items (FIFO)
        self._episodic = self._episodic[-self.max_episodic:]

elif memory_type == MemoryType.SEMANTIC:
    self._semantic[memory.memory_id] = memory
    # Trim if exceeds max
    if len(self._semantic) > self.max_semantic:
        # Remove least important items
        sorted_items = sorted(
            self._semantic.values(),
            key=lambda m: m.importance
        )
        to_remove = sorted_items[:len(sorted_items) - self.max_semantic]
        for item in to_remove:
            self._semantic.pop(item.memory_id, None)
```

### 2. Add Time-Based Expiration

```python
# Add to MemoryItem
max_age_days: Optional[int] = None  # Optional max age in days

# Add cleanup method
def cleanup_expired(self, max_age_days: int = 30) -> int:
    """Remove memories older than max_age_days."""
    from datetime import timedelta
    cutoff = datetime.now() - timedelta(days=max_age_days)

    removed = 0

    # Clean short-term
    self._short_term = [m for m in self._short_term if m.timestamp > cutoff]

    # Clean long-term
    to_remove = [
        mid for mid, m in self._long_term.items()
        if m.timestamp <= cutoff
    ]
    for mid in to_remove:
        self._long_term.pop(mid, None)
        removed += 1

    # Clean episodic
    before = len(self._episodic)
    self._episodic = [m for m in self._episodic if m.timestamp > cutoff]
    removed += before - len(self._episodic)

    # Clean semantic
    to_remove = [
        mid for mid, m in self._semantic.items()
        if m.timestamp <= cutoff
    ]
    for mid in to_remove:
        self._semantic.pop(mid, None)
        removed += 1

    if removed > 0:
        self._persist()

    return removed
```

### 3. Add Memory Pressure Handling

```python
# Add to AgentMemory
def check_memory_pressure(self) -> Dict[str, Any]:
    """Check if memory usage is high."""
    total = (
        len(self._short_term) +
        len(self._long_term) +
        len(self._episodic) +
        len(self._semantic)
    )

    max_total = (
        self.max_short_term +
        self.max_long_term +
        (self.max_episodic if hasattr(self, 'max_episodic') else float('inf')) +
        (self.max_semantic if hasattr(self, 'max_semantic') else float('inf'))
    )

    usage_ratio = total / max_total if max_total != float('inf') else 0

    return {
        "total_memories": total,
        "usage_ratio": usage_ratio,
        "under_pressure": usage_ratio > 0.8,
        "breakdown": {
            "short_term": len(self._short_term),
            "long_term": len(self._long_term),
            "episodic": len(self._episodic),
            "semantic": len(self._semantic)
        }
    }

def handle_memory_pressure(self) -> int:
    """Automatically clean up when under memory pressure."""
    pressure = self.check_memory_pressure()

    if not pressure["under_pressure"]:
        return 0

    # Clean up old memories first
    removed = self.cleanup_expired(max_age_days=7)

    # If still under pressure, remove least important
    if self.check_memory_pressure()["under_pressure"]:
        # Remove least important from all types
        all_memories = (
            list(self._short_term) +
            list(self._long_term.values()) +
            list(self._episodic) +
            list(self._semantic.values())
        )
        all_memories.sort(key=lambda m: m.importance)

        # Remove bottom 10%
        to_remove = all_memories[:len(all_memories) // 10]
        for memory in to_remove:
            self.forget(memory.memory_id)
            removed += 1

    return removed
```

### 4. Add Periodic Cleanup

```python
# Add to Agent class
import asyncio
from datetime import timedelta

async def _periodic_memory_cleanup(self, interval_minutes: int = 60):
    """Periodic memory cleanup task."""
    while True:
        await asyncio.sleep(interval_minutes * 60)
        if self.memory:
            self.memory.handle_memory_pressure()
```

## Summary

**Current Status:** ⚠️ **Partially Well-Handled**

- ✅ Cache: Well managed
- ✅ Prompt Context: Well managed
- ✅ Short-term/Long-term Memory: Well managed
- ❌ Episodic/Semantic Memory: **UNBOUNDED - MEMORY LEAK RISK**
- ❌ No automatic cleanup
- ❌ No time-based expiration
- ❌ No memory pressure handling

**Priority:** **HIGH** - Episodic and Semantic memory can cause memory leaks in long-running agents.

