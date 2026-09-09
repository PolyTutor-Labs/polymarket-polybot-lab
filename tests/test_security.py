"""Security helpers: redaction and the secret scanner.

Does not exercise live trading, strategies, or the executor path.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from urllib.error import URLError

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT / "scripts" / "security"))

import notifier as notifier_mod
from check_secrets import findings_in_text, main as secret_scan_main, scan_repo
from notifier import TelegramNotifier, redact


def test_redact_hex_key_and_telegram_token():
    key = "0x" + "ab" * 32
    token = "123456789:AA" + "B" * 35
    text = redact(f"leak {key} and {token}")
    assert "abab" not in text
    assert "123456789:" not in text
    assert "[REDACTED_KEY]" in text
    assert "[REDACTED_TOKEN]" in text


def test_redact_telegram_url_and_known_token():
    token = "123456789:AA" + "C" * 35
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    text = redact(f"HTTP Error 400: {url}", token)
    assert token not in text
    assert "api.telegram.org/bot[REDACTED_TOKEN]" in text or "[REDACTED]" in text


def test_telegram_send_failure_does_not_log_token(caplog, monkeypatch):
    token = "123456789:AA" + "D" * 35
    instance = TelegramNotifier(token, "42")

    def _boom(_url, _payload, timeout=5):
        raise URLError(f"https://api.telegram.org/bot{token}/sendMessage")

    caplog.set_level(logging.WARNING, logger="notify")
    monkeypatch.setattr(notifier_mod.urllib.request, "urlopen", _boom)
    instance.send("hello")

    combined = " ".join(r.getMessage() for r in caplog.records)
    assert token not in combined
    assert "telegram send failed" in combined


def test_secret_scanner_ignores_placeholders_and_synthetic_hex():
    text = "\n".join([
        "PRIVATE_KEY=",
        "TELEGRAM_BOT_TOKEN=",
        'PRIVATE_KEY="0x" + "a" * 64',
        "0x" + "a" * 64,
        "CLOB_HOST=https://clob.polymarket.com",
    ])
    assert findings_in_text(text, "fake.env") == []


def test_secret_scanner_flags_value_shaped_secrets():
    pem = "-----BEGIN " + "RSA PRIVATE KEY-----"
    aws = "AKIA" + "B" * 16
    hits = findings_in_text(f"{pem}\nkey={aws}\n", "leak.txt")
    cats = {h.category for h in hits}
    assert "pem_private_key" in cats
    assert "aws_access_key" in cats
    # Never persist or echo the fixture values in assertions beyond membership.
    assert all(h.path == "leak.txt" for h in hits)


def test_repo_secret_scan_is_clean():
    findings = scan_repo(_ROOT)
    assert findings == [], [
        f"{f.path}:{f.line}:{f.category}" for f in findings
    ]


def test_secret_scanner_flags_github_slack_telegram_shapes():
    github = "ghp_" + "A" * 36
    slack = "xoxb-" + "1234567890-123456789012-abcdefghij"
    telegram = "123456789:AA" + "E" * 35
    hits = findings_in_text(
        f"token={github}\nhook={slack}\nbot={telegram}\n",
        "leak.txt",
    )
    cats = {h.category for h in hits}
    assert "github_token" in cats
    assert "slack_token" in cats
    assert "telegram_bot_token" in cats
    assert all(h.path == "leak.txt" for h in hits)


def test_secret_scanner_flags_assignment_of_non_placeholder():
    body = "API_SECRET=" + '"not-a-placeholder-value"\n'
    hits = findings_in_text(body, "env.txt")
    assert any(h.category == "credential_assignment" for h in hits)


def test_secret_scanner_cli_exits_zero_on_clean_repo():
    assert secret_scan_main() == 0
