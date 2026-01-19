#!/usr/bin/env python3
"""
Documentation Search Utility

Search SDK documentation from command line or programmatically.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple


class DocumentationSearcher:
    """Search SDK documentation."""
    
    def __init__(self, docs_dir: Optional[str] = None):
        """
        Initialize searcher.
        
        Args:
            docs_dir: Path to docs directory (default: current directory)
        """
        if docs_dir is None:
            # Assume we're in docs/guide/ directory, go up to docs/
            self.docs_dir = Path(__file__).parent.parent
        else:
            self.docs_dir = Path(docs_dir)
        
        self.docs_dir = self.docs_dir.resolve()
    
    def search(self, query: str, file_pattern: str = "*.md") -> List[Dict[str, any]]:
        """
        Search documentation files.
        
        Args:
            query: Search query (supports regex)
            file_pattern: File pattern to search (default: *.md)
            
        Returns:
            List of matches with file path, line number, and context
        """
        results = []
        query_re = re.compile(query, re.IGNORECASE)
        
        for file_path in self.docs_dir.rglob(file_pattern):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        if query_re.search(line):
                            # Get context (previous and next lines)
                            context_before = []
                            context_after = []
                            
                            # Read file again for context
                            with open(file_path, 'r', encoding='utf-8') as f2:
                                lines = f2.readlines()
                                start = max(0, line_num - 3)
                                end = min(len(lines), line_num + 2)
                                context = lines[start:end]
                            
                            results.append({
                                "file": str(file_path.relative_to(self.docs_dir)),
                                "line": line_num,
                                "match": line.strip(),
                                "context": context
                            })
            except Exception as e:
                # Skip files that can't be read
                continue
        
        return results
    
    def search_by_topic(self, topic: str) -> List[str]:
        """
        Find documentation files related to a topic.
        
        Args:
            topic: Topic to search for
            
        Returns:
            List of relevant file paths
        """
        topic_lower = topic.lower()
        relevant_files = []
        
        # Topic to file mapping
        topic_map = {
            "agent": ["agno_agent_framework", "agent"],
            "gateway": ["litellm_gateway", "gateway"],
            "rag": ["rag"],
            "prompt": ["prompt"],
            "config": ["config", "configuration"],
            "error": ["error", "exception", "troubleshooting"],
            "integration": ["integration", "nats", "otel", "codec"],
            "architecture": ["architecture"],
            "troubleshooting": ["troubleshooting"],
            "example": ["example", "use_case"]
        }
        
        # Find matching files
        for file_path in self.docs_dir.rglob("*.md"):
            file_str = str(file_path).lower()
            
            # Check if topic matches
            if topic_lower in file_str:
                relevant_files.append(str(file_path.relative_to(self.docs_dir)))
                continue
            
            # Check topic map
            for key, patterns in topic_map.items():
                if key in topic_lower:
                    if any(p in file_str for p in patterns):
                        relevant_files.append(str(file_path.relative_to(self.docs_dir)))
                        break
        
        return list(set(relevant_files))  # Remove duplicates
    
    def find_function_docs(self, function_name: str) -> List[Dict[str, any]]:
        """
        Find documentation for a specific function.
        
        Args:
            function_name: Name of function to find
            
        Returns:
            List of matches
        """
        # Search for function name in code blocks and text
        pattern = rf"\b{re.escape(function_name)}\b"
        return self.search(pattern)
    
    def list_all_docs(self) -> Dict[str, List[str]]:
        """
        List all documentation files organized by category.
        
        Returns:
            Dictionary mapping categories to file lists
        """
        categories = {
            "guides": [],
            "architecture": [],
            "components": [],
            "integration": [],
            "troubleshooting": [],
            "other": []
        }
        
        for file_path in self.docs_dir.rglob("*.md"):
            rel_path = str(file_path.relative_to(self.docs_dir))
            
            if "guide" in rel_path.lower():
                categories["guides"].append(rel_path)
            elif "architecture" in rel_path:
                categories["architecture"].append(rel_path)
            elif "components" in rel_path:
                categories["components"].append(rel_path)
            elif "integration" in rel_path:
                categories["integration"].append(rel_path)
            elif "troubleshooting" in rel_path:
                categories["troubleshooting"].append(rel_path)
            else:
                categories["other"].append(rel_path)
        
        return categories


def main():
    """Command-line interface."""
    import sys
    
    searcher = DocumentationSearcher()
    
    if len(sys.argv) < 2:
        print("Usage: python search_docs.py <command> [args...]")
        print("\nCommands:")
        print("  search <query>          - Search for text in docs")
        print("  topic <topic>           - Find docs by topic")
        print("  function <name>         - Find function documentation")
        print("  list                    - List all documentation files")
        return
    
    command = sys.argv[1]
    
    if command == "search":
        if len(sys.argv) < 3:
            print("Usage: python search_docs.py search <query>")
            return
        
        query = sys.argv[2]
        results = searcher.search(query)
        
        print(f"\nFound {len(results)} matches for '{query}':\n")
        for result in results[:20]:  # Limit to 20 results
            print(f"📄 {result['file']}:{result['line']}")
            print(f"   {result['match'][:100]}...")
            print()
        
        if len(results) > 20:
            print(f"... and {len(results) - 20} more results")
    
    elif command == "topic":
        if len(sys.argv) < 3:
            print("Usage: python search_docs.py topic <topic>")
            return
        
        topic = sys.argv[2]
        files = searcher.search_by_topic(topic)
        
        print(f"\nDocumentation for '{topic}':\n")
        for file in files:
            print(f"  📄 {file}")
    
    elif command == "function":
        if len(sys.argv) < 3:
            print("Usage: python search_docs.py function <function_name>")
            return
        
        func_name = sys.argv[2]
        results = searcher.find_function_docs(func_name)
        
        print(f"\nDocumentation for '{func_name}':\n")
        for result in results[:10]:
            print(f"📄 {result['file']}:{result['line']}")
            print(f"   {result['match'][:100]}...")
            print()
    
    elif command == "list":
        categories = searcher.list_all_docs()
        
        print("\n📚 All Documentation Files:\n")
        for category, files in categories.items():
            if files:
                print(f"{category.upper()}:")
                for file in sorted(files):
                    print(f"  📄 {file}")
                print()


if __name__ == "__main__":
    main()

