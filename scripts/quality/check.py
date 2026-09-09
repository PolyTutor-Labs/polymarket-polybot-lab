#!/usr/bin/env python3
"""Educational quality gates for the paper / DRY_RUN research lab.

Runs syntax compile, pytest, the existing secret scanner, and an internal
markdown-link check. Does not deploy, trade, or talk to exchanges.

    python scripts/quality/check.py
"""
from __future__ import annotations

import ast
import re
import subprocess
import sys
from pathlib import Path

_MD_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
_SKIP_HREF = ("http://", "https://", "mailto:", "#")
_SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache"}


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def _run(title: str, argv: list[str], cwd: Path) -> int:
    print(f"==> {title}")
    print(" ".join(argv))
    completed = subprocess.run(argv, cwd=cwd)
    if completed.returncode != 0:
        print(f"{title}: FAILED (exit {completed.returncode})")
    else:
        print(f"{title}: OK")
    return completed.returncode


def python_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*.py"):
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        files.append(path)
    return sorted(files)


def check_syntax(root: Path) -> int:
    """Lightweight parse/import-safety check: every .py file is valid AST."""
    failed: list[str] = []
    for path in python_files(root):
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            failed.append(f"{path.relative_to(root)}: {exc.msg} (line {exc.lineno})")
    if failed:
        for item in failed:
            print(f"SYNTAX  {item}")
        print(f"syntax: FAILED ({len(failed)} file(s))")
        return 1
    print(f"syntax: OK ({len(python_files(root))} files parsed)")
    return 0


def markdown_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*.md"):
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        files.append(path)
    return sorted(files)


def check_markdown_links(root: Path) -> int:
    """Resolve relative markdown links. External URLs are not fetched."""
    missing: list[str] = []
    checked = 0
    for md in markdown_files(root):
        text = md.read_text(encoding="utf-8")
        for match in _MD_LINK.finditer(text):
            href = match.group(1).strip().split()[0]
            if not href or href.startswith(_SKIP_HREF):
                continue
            href = href.split("#", 1)[0]
            if not href:
                continue
            checked += 1
            target = (md.parent / href).resolve()
            try:
                target.relative_to(root.resolve())
            except ValueError:
                missing.append(f"{md.relative_to(root)} -> {href} (escapes repo)")
                continue
            if not target.exists():
                missing.append(f"{md.relative_to(root)} -> {href}")
    if missing:
        for item in missing:
            print(f"LINK    {item}")
        print(f"markdown-links: FAILED ({len(missing)} missing)")
        return 1
    print(f"markdown-links: OK ({checked} internal links)")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    root = repo_root()
    singles = {
        "syntax": lambda: check_syntax(root),
        "links": lambda: check_markdown_links(root),
    }
    if len(args) == 1 and args[0] in singles:
        return singles[args[0]]()
    if args:
        print("usage: python scripts/quality/check.py [syntax|links]")
        return 2

    py = sys.executable
    steps = [
        ("compileall", [py, "-m", "compileall", "-q", "."]),
        ("syntax", None),
        ("pytest", [py, "-m", "pytest", "tests/", "-q"]),
        ("secret-scan", [py, str(root / "scripts" / "security" / "check_secrets.py")]),
        ("markdown-links", None),
    ]
    failed = 0
    for title, command in steps:
        if title == "syntax":
            code = check_syntax(root)
        elif title == "markdown-links":
            code = check_markdown_links(root)
        else:
            assert command is not None
            code = _run(title, command, root)
        if code != 0:
            failed = 1
    if failed:
        print("quality: FAILED")
        return 1
    print("quality: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
