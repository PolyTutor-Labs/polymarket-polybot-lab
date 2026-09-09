"""Helpers, parsers, and educational CLI/reconciler behavior.

Existing behavior only. Does not implement live reconciliation or approve.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT / "strategies"))

from config import Settings
from fees import taker_fee, round_to_tick
from models import BookTop, MarketWindow, Order, Outcome, Side
from notifier import TelegramNotifier
from reconciler import Reconciler
from risk_gate import RiskGate
from store import Store
from timeutil import Clock, market_slug


def _load_bot():
    spec = importlib.util.spec_from_file_location("polybot_cli", _ROOT / "bot.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_market_slug_renders_window_start():
    assert market_slug("bitcoin-up-or-down-{ts}", 600) == "bitcoin-up-or-down-600"


def test_clock_sync_stores_server_offset():
    clock = Clock()
    clock.sync(1_000.0, 990.0)
    assert clock.server_offset_s == pytest.approx(10.0)


def test_book_mid_and_order_notional():
    book = BookTop("tok", 0.40, 0.50, 10, 10)
    assert book.mid == pytest.approx(0.45)
    market = MarketWindow("slug", "cid", "y", "n", 600, 900, 200, 0.01, 1)
    order = Order(market, Outcome.YES, Side.BUY, 0.40, 2.5, "t")
    assert order.notional == pytest.approx(1.0)
    assert order.client_id


def test_taker_fee_scales_with_size():
    assert taker_fee(0.30, 10, 200) == pytest.approx(0.02 * 0.30 * 10)


def test_round_to_tick_rejects_non_positive_tick():
    with pytest.raises(ValueError):
        round_to_tick(0.48, 0.0)


def test_notifier_disabled_without_token_or_chat():
    assert TelegramNotifier("", "").enabled is False
    assert TelegramNotifier("token", "").enabled is False
    assert TelegramNotifier("", "42").enabled is False
    assert TelegramNotifier("token", "42").enabled is True


def test_reconciler_dry_run_skips_exchange():
    store = Store(":memory:")
    gate = RiskGate(
        max_daily_loss=5,
        max_consecutive_losses=3,
        max_open_exposure=10,
        kill_switch_file=str(_ROOT / "tests" / "__missing_kill_switch__"),
    )
    rec = Reconciler(store, gate, dry_run=True)
    assert rec.exchange_open_positions() is None
    assert rec.run() is True
    assert not gate.halted
    store.close()


def test_reconciler_live_path_is_unimplemented():
    store = Store(":memory:")
    gate = RiskGate(
        max_daily_loss=5,
        max_consecutive_losses=3,
        max_open_exposure=10,
        kill_switch_file=str(_ROOT / "tests" / "__missing_kill_switch__"),
    )
    rec = Reconciler(store, gate, dry_run=False)
    with pytest.raises(NotImplementedError):
        rec.exchange_open_positions()
    store.close()


def test_approve_is_noop_when_dry_run(capsys):
    bot = _load_bot()

    def _settings() -> Settings:
        return Settings()

    bot.load_settings = _settings  # type: ignore[method-assign]
    bot.cmd_approve()
    out = capsys.readouterr().out
    assert "DRY_RUN=true" in out
    assert "Nothing to do" in out


def test_approve_stub_exits_when_live_gates_pass():
    bot = _load_bot()

    def _settings() -> Settings:
        return Settings(
            dry_run=False,
            live_trading_ack="I_UNDERSTAND_THE_RISKS",
            private_key="0x" + "a" * 64,
        )

    bot.load_settings = _settings  # type: ignore[method-assign]
    with pytest.raises(SystemExit) as exc:
        bot.cmd_approve()
    assert exc.value.code == 1
