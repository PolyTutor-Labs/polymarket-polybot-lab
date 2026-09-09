"""Config loading, path handling, and store behavior.

Existing paper-lab behavior only. Does not change settings defaults or
trading paths.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from config import (
    LIVE_ACK_PHRASE,
    Settings,
    data_dir,
    load_settings,
    repo_root,
    resolve_data_path,
    resolve_ops_path,
)
from executor import DryRunExecutor, build_executor
from store import Store


def test_repo_root_is_cwd_independent(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert repo_root() == _ROOT
    assert repo_root().joinpath("src", "config.py").is_file()


def test_data_dir_defaults_to_repo_root(monkeypatch):
    monkeypatch.delenv("POLYBOT_DATA_DIR", raising=False)
    assert data_dir({}) == repo_root()
    assert data_dir({"POLYBOT_DATA_DIR": ""}) == repo_root()


def test_relative_polybot_data_dir_joins_repo_root(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    resolved = data_dir({"POLYBOT_DATA_DIR": "lab-data"})
    assert resolved == (repo_root() / "lab-data").resolve()


def test_tilde_data_path_is_absolute(monkeypatch):
    monkeypatch.setenv("HOME", "/tmp/polybot-home")
    raw = resolve_data_path("~/state.sqlite3")
    assert Path(raw).is_absolute()
    assert raw.endswith("state.sqlite3")


def test_resolve_ops_path_relative_and_absolute(tmp_path):
    assert Path(resolve_ops_path("KILL_SWITCH")) == repo_root() / "KILL_SWITCH"
    abs_ks = tmp_path / "STOP"
    assert resolve_ops_path(str(abs_ks)) == str(abs_ks)


def test_empty_env_values_are_ignored():
    s = load_settings({"PRIVATE_KEY": "", "BANKROLL": "250", "DRY_RUN": ""})
    assert s.private_key == ""
    assert s.bankroll == 250.0
    assert s.dry_run is True


def test_bool_env_parsing():
    assert load_settings({"MAKER_ENABLED": "0"}).maker_enabled is False
    assert load_settings({"MAKER_ENABLED": "yes"}).maker_enabled is True
    assert load_settings({"DRY_RUN": "false"}).dry_run is False
    assert load_settings({"DRY_RUN": "ON"}).dry_run is True


def test_code_only_defaults_are_not_read_from_env():
    s = load_settings({
        "CHAIN_ID": "1",
        "WINDOW_SECONDS": "60",
        "MARKET_SLUG_TEMPLATE": "other-{ts}",
        "TICK_SIZE": "0.001",
        "MIN_ORDER_SIZE": "9",
        "LOG_LEVEL": "DEBUG",
    })
    assert s.chain_id == 137
    assert s.window_seconds == 300
    assert s.market_slug_template == "bitcoin-up-or-down-{ts}"
    assert s.tick_size == 0.01
    assert s.min_order_size == 1.0
    assert s.log_level == "INFO"


def test_load_settings_does_not_read_dotenv_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text(
        "DRY_RUN=false\nLIVE_TRADING_ACK=" + LIVE_ACK_PHRASE + "\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("DRY_RUN", raising=False)
    monkeypatch.delenv("LIVE_TRADING_ACK", raising=False)
    s = load_settings()
    assert s.dry_run is True
    assert s.live_trading_ack == ""


def test_is_live_requires_both_gates():
    assert Settings().is_live is False
    assert Settings(dry_run=False).is_live is False
    assert Settings(dry_run=False, live_trading_ack=LIVE_ACK_PHRASE).is_live is True
    assert Settings(dry_run=True, live_trading_ack=LIVE_ACK_PHRASE).is_live is False


def test_assert_live_allowed_is_noop_in_dry_run():
    Settings().assert_live_allowed()


def test_daily_loss_pct_cannot_exceed_five_percent():
    with pytest.raises(ValidationError):
        Settings(max_daily_loss_pct=0.06)
    with pytest.raises(ValidationError):
        Settings(max_daily_loss_pct=0.0)


def test_quote_cancel_must_be_before_quote_min():
    with pytest.raises(ValidationError):
        Settings(quote_cancel_remaining_s=60, quote_min_remaining_s=60)


def test_telegram_token_redacted_in_repr():
    token = "123456789:AA" + "BBCCDDEEFFGGHHIIJJKKLLMMNNOOPPQQQ"
    s = Settings(telegram_bot_token=token)
    assert "AABBCC" not in repr(s)


def test_build_executor_defaults_to_dry_run():
    ex = build_executor(Settings())
    assert isinstance(ex, DryRunExecutor)


def test_store_record_order_is_idempotent(tmp_path):
    store = Store(str(tmp_path / "lab.sqlite3"))
    kwargs = dict(
        client_id="abc",
        market_slug="btc-test",
        window_start=600,
        outcome="YES",
        side="BUY",
        price=0.45,
        size=2.0,
        strategy="pair_cost_arb",
        dry_run=True,
    )
    assert store.record_order(**kwargs) is True
    assert store.record_order(**kwargs) is False
    n = store.conn.execute("SELECT COUNT(*) c FROM orders").fetchone()["c"]
    assert n == 1
    store.close()


def test_store_kv_roundtrip(tmp_path):
    store = Store(str(tmp_path / "lab.sqlite3"))
    assert store.kv_get("halt") is None
    store.kv_set("halt", "kill_switch")
    assert store.kv_get("halt") == "kill_switch"
    store.kv_set("halt", "reviewed")
    assert store.kv_get("halt") == "reviewed"
    store.kv_delete("halt")
    assert store.kv_get("halt") is None
    store.close()


def test_store_creates_parent_directories(tmp_path):
    db = tmp_path / "nested" / "state" / "lab.sqlite3"
    store = Store(str(db))
    store.close()
    assert db.exists()


def test_memory_store_and_stats():
    store = Store(":memory:")
    assert store.path == ":memory:"
    store.record_order(
        client_id="m1", market_slug="m", window_start=0, outcome="YES",
        side="BUY", price=0.4, size=1.0, strategy="t", dry_run=True,
    )
    store.record_fill("m1", 0.4, 1.0, 0.01)
    store.record_settlement("m1", outcome_won=False, pnl=-0.41)
    stats = store.stats()
    assert stats["orders"] == 1
    assert stats["settled"] == 1
    assert stats["pnl"] == pytest.approx(-0.41)
    assert stats["fees"] == pytest.approx(0.01)
    assert store.daily_pnl(0) == pytest.approx(-0.41)
    assert store.total_pnl() == pytest.approx(-0.41)
    store.close()


def test_fill_for_order_aggregates_size_and_fees():
    store = Store(":memory:")
    store.record_order(
        client_id="f1", market_slug="m", window_start=0, outcome="YES",
        side="BUY", price=0.5, size=3.0, strategy="t", dry_run=True,
    )
    store.conn.execute(
        "INSERT INTO fills (client_id, ts, price, size, fee_paid) VALUES (?,?,?,?,?)",
        ("f1", 1, 0.50, 1.0, 0.01),
    )
    store.conn.execute(
        "INSERT INTO fills (client_id, ts, price, size, fee_paid) VALUES (?,?,?,?,?)",
        ("f1", 2, 0.40, 1.0, 0.02),
    )
    store.conn.commit()
    row = store.fill_for_order("f1")
    assert row is not None
    assert row["size"] == pytest.approx(2.0)
    assert row["fee_paid"] == pytest.approx(0.03)
    assert row["price"] == pytest.approx(0.45)
    assert store.fill_for_order("missing") is None
    store.close()


def test_cancel_stale_open_orders_leaves_filled(tmp_path):
    store = Store(str(tmp_path / "lab.sqlite3"))
    store.record_order(
        client_id="open1", market_slug="m", window_start=0, outcome="YES",
        side="BUY", price=0.4, size=1.0, strategy="pair_cost_maker", dry_run=True,
    )
    store.set_order_status("open1", "open")
    store.record_order(
        client_id="fill1", market_slug="m", window_start=0, outcome="NO",
        side="BUY", price=0.4, size=1.0, strategy="pair_cost_maker", dry_run=True,
    )
    store.record_fill("fill1", 0.4, 1.0, 0.0)
    n = store.cancel_stale_open_orders()
    assert n == 1
    statuses = {
        r["client_id"]: r["status"]
        for r in store.conn.execute("SELECT client_id, status FROM orders")
    }
    assert statuses["open1"] == "cancelled"
    assert statuses["fill1"] == "filled"
    store.close()


def test_store_relative_path_uses_env_not_process_environ_leak(tmp_path, monkeypatch):
    """Store constructor reads POLYBOT_DATA_DIR from os.environ via resolve_data_path."""
    monkeypatch.setenv("POLYBOT_DATA_DIR", str(tmp_path))
    cwd = tmp_path / "elsewhere"
    cwd.mkdir()
    monkeypatch.chdir(cwd)
    store = Store("from-env.sqlite3")
    store.close()
    assert (tmp_path / "from-env.sqlite3").exists()
    assert not (cwd / "from-env.sqlite3").exists()


def test_load_settings_does_not_mutate_os_environ(monkeypatch):
    monkeypatch.delenv("BANKROLL", raising=False)
    before = dict(os.environ)
    load_settings({"BANKROLL": "333"})
    assert os.environ.get("BANKROLL") is None
    assert os.environ == before
