# Getting started (DRY_RUN)

Paper-trade the live Polymarket BTC 5-minute order books. The engine defaults
to `DRY_RUN=true`. No LLM is on the execution path.

## Install and run

Install from the repository root. `python bot.py` may be launched from any
working directory — imports and runtime files resolve from the repo root
via `Path(__file__)`, not the process cwd.

```bash
pip install -r requirements.txt
cp .env.example .env          # placeholders only
set -a; source .env; set +a   # required — load_settings() does not read .env
python -m pytest tests/ -q    # all tests must pass
python scripts/security/check_secrets.py
python bot.py run             # paper-trades the live order books
python bot.py status          # PnL, budget left, streak, halt state
```

`bot.py` stays at the repo root so these commands do not change. Engine
modules load from `src/`; strategies load from `strategies/`.

Stay on DRY_RUN for paper research. Weeks of simulated trades are for
learning the engine, not a go-live countdown. Live mode remains High risk
and incomplete (see below).

## Environment notes

`.env.example` documents the environment knobs `load_settings()` actually
reads, plus `POLYBOT_DATA_DIR` (path resolution only). Code-only defaults
(`chain_id`, `window_seconds`, `market_slug_template`, `tick_size`,
`min_order_size`, `log_level`) are **not** loaded from the environment —
setting them in `.env` has no effect. See [SECURITY.md](../SECURITY.md).

`load_settings()` in `src/config.py` reads `os.environ` (it does not
auto-load a `.env` file). Export variables or `set -a; source .env; set +a`
before `python bot.py run`.

SQLite state (`DB_PATH`, default `polybot.sqlite3`) is written under
`POLYBOT_DATA_DIR` when that variable is set, otherwise under the
repository root. `KILL_SWITCH` (or `KILL_SWITCH_FILE`) is resolved against
the repository root. Relative paths do not follow the process cwd. Both
the database and the kill-switch file are gitignored.

## Going live (not supported; deliberately incomplete)

Live trading is **not** part of this educational lab. The security notes
treat live mode as High risk: the signing key is held in-process, `CLOB_HOST`
is not allowlisted, the live reconciler raises `NotImplementedError`, and
`py-clob-client` is unpinned. See [SECURITY.md](../SECURITY.md).

This is not a production checklist. If you still read the educational live
path, the original engine gates remain:

1. **Dedicated wallet** funded with bankroll only. Key in env at runtime,
   never in files the agent can read, never in chat with any agent.
2. Audit + pin `py-clob-client` in `requirements.txt`.
3. One-time USDC (ERC-20) + CTF (ERC-1155) allowance approvals
   (`python bot.py approve` — wire to audited contract addresses first).
4. `.env`: `DRY_RUN=false` **and** `LIVE_TRADING_ACK=I_UNDERSTAND_THE_RISKS`.
   Either one alone refuses to start.
5. Verify the market's tie rule (flat close). The engine treats
   close == open as DOWN; confirm against the live market's resolution
   source before trusting DRY_RUN accounting.
6. Run on a VPS, not a laptop. Keep `MAX_BET=2` until the analyst report
   says otherwise.

**Emergency stop:** `touch KILL_SWITCH` at the repository root — next
risk-gate check halts the engine. Restart requires removing the file,
`python bot.py reset`, and a human review of the halt reason.

## What this deliberately does NOT do

- No LLM calls at trade time (latency + nondeterminism = exit liquidity)
- No martingale / DCA-into-losers (averaging down on a 5-minute binary is a
  tail-risk machine, not a strategy)
- No chasing: limit orders at the observed ask, FOK, no repricing loop
- No directional trading live until calibration proves the model
- No "recover today's loss" logic of any kind: when the budget is spent,
  the day is over

## Known limitations (accepted, documented)

- Window open/close prices come from the Binance spot feed sampled at the
  window boundary — an approximation of the market's official resolution
  source. Good enough for DRY_RUN accounting.
- The live reconciler is **not implemented** (`NotImplementedError`). It is
  not a source of truth and not production-ready.
- DRY_RUN fills are pessimistic (displayed size only, no price improvement)
  but cannot model queue position or being quoted against.

## Compliance note

Polymarket geo-blocks several jurisdictions (Italy included). Operating
through a blocked region risks account restriction and frozen funds.
That risk is yours and no engineering mitigates it.

## Offline review

After paper sessions, use [analyst-prompt.md](analyst-prompt.md) as a
read-only nightly review. The LLM stays outside the execution path.
