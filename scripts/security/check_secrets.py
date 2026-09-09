#!/usr/bin/env python3
"""Scan git-tracked files for committed secret *values*.

Never prints matched values. Prints filename, category, severity, line
number only. Exits 1 when a finding is present.

This is a cheap educational-lab guard, not a substitute for gitleaks or
a full history rewrite. Placeholders, empty assignments, and synthetic
test fixtures (repeated hex) are ignored.
"""
from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

# Categories are value-shaped. Keyword mentions (PRIVATE_KEY=) with an
# empty or placeholder right-hand side are not findings.
_PEM = re.compile(r"-----BEGIN [A-Z0-9 ]{0,40}PRIVATE KEY-----")
_AWS_KEY = re.compile(r"\bAKIA[0-9A-Z]{16}\b")
_GITHUB = re.compile(
    r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}\b"
    r"|\bgithub_pat_[A-Za-z0-9_]{20,}\b"
)
_SLACK = re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")
_TELEGRAM = re.compile(r"\b\d{8,10}:[A-Za-z0-9_-]{35,}\b")
_HEX_KEY = re.compile(r"\b(?:0x)?([0-9a-fA-F]{64})\b")
_ASSIGN = re.compile(
    r"(?i)\b(PRIVATE_KEY|TELEGRAM_BOT_TOKEN|API_SECRET|SECRET_KEY|"
    r"PASSWORD|MNEMONIC|API_KEY|BEARER(?:_TOKEN)?)\b\s*[:=]\s*"
    r"(?P<val>'[^']{8,}'|\"[^\"]{8,}\"|[^\s#'\"]{8,})"
)
_PLACEHOLDER = re.compile(
    r"(?i)^(none|null|todo|changeme|xxx|placeholder|your[-_].*|"
    r"<.*>|\$\{?[\w.]+\}?|\.\.\.)$"
)

_SKIP_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".woff",
                  ".woff2", ".ttf", ".eot", ".mp4", ".zip", ".gz", ".whl"}


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    category: str
    severity: str


def _is_synthetic_hex(hex_body: str) -> bool:
    h = hex_body.lower()
    if len(set(h)) == 1:
        return True
    for n in (2, 4, 8):
        if len(h) % n == 0 and h == h[:n] * (len(h) // n):
            return True
    return False


def _is_placeholder(raw: str) -> bool:
    val = raw.strip().strip("'\"").strip()
    if not val:
        return True
    if _PLACEHOLDER.match(val):
        return True
    # Constructed fixtures such as "0x" + "a" * 64
    if "+" in val or "*" in val:
        return True
    return False


def findings_in_text(text: str, path: str) -> list[Finding]:
    found: list[Finding] = []
    for i, line in enumerate(text.splitlines(), 1):
        if _PEM.search(line):
            found.append(Finding(path, i, "pem_private_key", "critical"))
        if _AWS_KEY.search(line):
            found.append(Finding(path, i, "aws_access_key", "critical"))
        if _GITHUB.search(line):
            found.append(Finding(path, i, "github_token", "critical"))
        if _SLACK.search(line):
            found.append(Finding(path, i, "slack_token", "high"))
        if _TELEGRAM.search(line):
            found.append(Finding(path, i, "telegram_bot_token", "high"))
        for m in _HEX_KEY.finditer(line):
            if not _is_synthetic_hex(m.group(1)):
                found.append(Finding(path, i, "hex_private_key", "critical"))
        for m in _ASSIGN.finditer(line):
            if not _is_placeholder(m.group("val")):
                found.append(Finding(path, i, "credential_assignment", "high"))
    return found


def repo_root() -> Path:
    out = subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"], text=True
    )
    return Path(out.strip())


def tracked_files(root: Path) -> list[Path]:
    out = subprocess.check_output(
        ["git", "ls-files", "-z"], cwd=root, text=True
    )
    paths = [root / p for p in out.split("\0") if p]
    return [p for p in paths if p.is_file() and p.suffix.lower() not in _SKIP_SUFFIXES]


def scan_repo(root: Path | None = None) -> list[Finding]:
    root = root or repo_root()
    findings: list[Finding] = []
    files = tracked_files(root)
    for path in files:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = str(path.relative_to(root))
        findings.extend(findings_in_text(text, rel))
    return findings


def main() -> int:
    root = repo_root()
    files = tracked_files(root)
    findings = scan_repo(root)
    print(f"secret-scan: {len(files)} tracked text files")
    if not findings:
        print("secret-scan: OK (no committed secret values)")
        return 0
    for f in findings:
        print(
            f"FINDING  {f.path}  line {f.line}  "
            f"category={f.category}  severity={f.severity}"
        )
    print(f"secret-scan: FAILED ({len(findings)} finding(s))")
    return 1


if __name__ == "__main__":
    sys.exit(main())
