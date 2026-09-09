"""Quality gates: collection, syntax, imports, docs, and lab hygiene.

Does not exercise strategies, PnL, or live trading. Documents existing
paper-lab behavior only.
"""
from __future__ import annotations

import ast
import compileall
import importlib
import re
import subprocess
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT / "strategies"))

import executor as executor_mod  # noqa: E402

_SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache"}
_ENGINE_MODULES = (
    "calibration",
    "config",
    "engine",
    "executor",
    "feeds",
    "fees",
    "models",
    "notifier",
    "reconciler",
    "risk_gate",
    "sizing",
    "store",
    "timeutil",
)
_STRATEGY_MODULES = ("strategy", "maker")
_MD_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def _python_files() -> list[Path]:
    files: list[Path] = []
    for path in _ROOT.rglob("*.py"):
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        files.append(path)
    return files


def test_pytest_ini_collects_only_tests_directory():
    ini = (_ROOT / "pytest.ini").read_text()
    assert "testpaths = tests" in ini
    assert "pythonpath = src strategies" in ini
    assert "norecursedirs" in ini
    assert "src" in ini and "strategies" in ini


def test_pytest_collects_no_src_or_scripts():
    out = subprocess.check_output(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        cwd=_ROOT,
        text=True,
    )
    for line in out.splitlines():
        if not line.strip() or line.startswith(("=", "<")):
            continue
        assert not line.startswith("src/")
        assert not line.startswith("strategies/")
        assert not line.startswith("scripts/")


def test_no_test_modules_live_outside_tests():
    stray = [
        str(p.relative_to(_ROOT))
        for p in _python_files()
        if p.name.startswith("test_") and "tests" not in p.parts
    ]
    assert stray == []


def test_all_python_files_compile():
    assert compileall.compile_dir(
        str(_ROOT),
        quiet=1,
        force=True,
        rx=re.compile(r"(/\.git/|/\.venv/|/venv/|/__pycache__/)"),
    )


def test_all_python_files_parse():
    for path in _python_files():
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


@pytest.mark.parametrize("name", _ENGINE_MODULES + _STRATEGY_MODULES)
def test_lab_modules_import(name: str):
    importlib.import_module(name)


def test_live_trading_clients_stay_optional():
    assert executor_mod.build_executor
    assert "py_clob_client" not in sys.modules
    assert "web3" not in sys.modules
    req = (_ROOT / "requirements.txt").read_text()
    for line in req.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        name = stripped.split("=", 1)[0].split(">", 1)[0].split("<", 1)[0]
        assert name not in {"py-clob-client", "web3"}


def test_requirements_stay_paper_lab_only():
    names: list[str] = []
    for line in (_ROOT / "requirements.txt").read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        names.append(stripped.split(">", 1)[0].split("<", 1)[0].split("=", 1)[0])
    assert names == ["pydantic", "pytest"]


def test_env_example_has_no_secret_values():
    text = (_ROOT / ".env.example").read_text()
    assert "PRIVATE_KEY=" in text
    assert "TELEGRAM_BOT_TOKEN=" in text
    for line in text.splitlines():
        if line.startswith("PRIVATE_KEY="):
            assert line == "PRIVATE_KEY="
        if line.startswith("TELEGRAM_BOT_TOKEN="):
            assert line == "TELEGRAM_BOT_TOKEN="
        if line.startswith("LIVE_TRADING_ACK="):
            assert line == "LIVE_TRADING_ACK="


def test_gitignore_covers_secrets_and_store():
    gi = (_ROOT / ".gitignore").read_text()
    for token in (".env", "*.sqlite3", "KILL_SWITCH", "*.pem", "*.key"):
        assert token in gi


def test_internal_markdown_links_resolve():
    missing: list[str] = []
    for md in _ROOT.rglob("*.md"):
        if any(part in _SKIP_DIRS for part in md.parts):
            continue
        for match in _MD_LINK.finditer(md.read_text(encoding="utf-8")):
            href = match.group(1).strip().split()[0]
            if not href or href.startswith(("http://", "https://", "mailto:", "#")):
                continue
            href = href.split("#", 1)[0]
            if not href:
                continue
            target = (md.parent / href).resolve()
            if not target.exists():
                missing.append(f"{md.relative_to(_ROOT)} -> {href}")
    assert missing == []


def test_quality_workflow_is_read_only():
    wf = (_ROOT / ".github" / "workflows" / "quality.yml").read_text()
    assert "permissions:" in wf
    assert "contents: read" in wf
    assert "contents: write" not in wf
    assert "deploy" not in wf.lower()
    assert "bot.py run" not in wf
    assert "scripts/security/check_secrets.py" in wf
    assert "python -m pytest tests/" in wf
    assert "compileall" in wf
