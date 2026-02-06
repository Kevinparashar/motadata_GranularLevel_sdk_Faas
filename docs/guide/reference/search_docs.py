"""
Simple documentation search helper.

This script is intentionally lightweight and dependency-free.
It helps developers quickly find where a topic is documented.

Usage examples:
    python docs/guide/search_docs.py list
    python docs/guide/search_docs.py search "create agent"
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DOC_ROOTS = [
    REPO_ROOT / "docs",
    REPO_ROOT / "src",
    REPO_ROOT / "examples",
]


def iter_md_files() -> list[Path]:
    files: list[Path] = []
    for root in DOC_ROOTS:
        if not root.exists():
            continue
        files.extend(root.rglob("*.md"))
    return sorted(files)


def cmd_list() -> None:
    for p in iter_md_files():
        print(p.relative_to(REPO_ROOT))


def cmd_search(query: str) -> None:
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    for p in iter_md_files():
        text = p.read_text(encoding="utf-8", errors="replace")
        if not pattern.search(text):
            continue
        print(p.relative_to(REPO_ROOT))


def main() -> None:
    parser = argparse.ArgumentParser(description="Search SDK documentation files")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="List all markdown documentation files")

    s = sub.add_parser("search", help="Search for a text phrase in markdown files")
    s.add_argument("query", help="Text to search (case-insensitive)")

    args = parser.parse_args()

    if args.cmd == "list":
        cmd_list()
        return

    if args.cmd == "search":
        cmd_search(args.query)
        return


if __name__ == "__main__":
    main()


