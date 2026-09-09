# Getting started (DRY_RUN)

Paper-trade the live Polymarket BTC 5-minute order books. The engine
defaults to `DRY_RUN=true`. No LLM is on the execution path.

This is an **educational** install path. **DRY_RUN first.** See
[paper-trading.md](paper-trading.md) for what the simulator does and
does not model.

## Install and run

Install from the repository root. `python bot.py` may be launched from
any working directory — imports and runtime files resolve from the repo
root via `Path(__file__)`, not the process cwd.

```bash
pip install -r requirements.txt
cp .env.example .env          # placeholders only
set -a; source .env; set +a   # required — load_settings() does not read .env
python -m compileall .
python -m pytest tests/ -q    # all tests must pass
python scripts/security/check_secrets.py
python scripts/quality/check.py
python bot.py run             # paper-trades the live order books
python bot.py status          # PnL, budget left, streak, halt state
```

`bot.py` stays at the repo root so these commands do not change. Engine
modules load from `src/`; strategies load from `strategies/`.

Stay on DRY_RUN for paper research. Simulated trades are for learning
the engine, not a go-live countdown. Live mode remains High risk and
incomplete ([limitations.md](limitations.md)).

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

## Emergency stop

`touch KILL_SWITCH` at the repository root — the next risk-gate check
halts the engine. Restart requires removing the file,
`python bot.py reset`, and a human review of the halt reason.

`python bot.py reset` does not delete `KILL_SWITCH`. Type `RESET` to
clear a persisted halt after you have reviewed logs and the store.

## Reading the live path (not supported)

Live trading is **not** part of this educational lab. The security notes
treat live mode as High risk: the signing key is held in-process,
`CLOB_HOST` is not allowlisted, the live reconciler raises
`NotImplementedError`, and `py-clob-client` is unpinned. See
[SECURITY.md](../SECURITY.md) and [limitations.md](limitations.md).

This is not a production checklist. The original engine still **gates**
the live path so students can read it:

1. Dedicated wallet funded with bankroll only. Key in env at runtime,
   never in files an agent can read, never in chat with any agent.
2. Audit + pin `py-clob-client` in `requirements.txt` (deferred).
3. One-time USDC (ERC-20) + CTF (ERC-1155) allowance approvals
   (`python bot.py approve` — **stub**, exits 1).
4. `.env`: `DRY_RUN=false` **and** `LIVE_TRADING_ACK=I_UNDERSTAND_THE_RISKS`.
   Either one alone refuses to start.
5. Verify the market's tie rule (flat close). The engine treats
   close == open as DOWN; confirm against the live market's resolution
   source before trusting DRY_RUN accounting.
6. Keep `MAX_BET` small. Paper results do not transfer.

## What this deliberately does not do

- No LLM calls at trade time
- No martingale / DCA-into-losers
- No chasing: limit orders at the observed ask, FOK, no taker reprice loop
- No directional trading live (`enable_directional_live` is false)
- No "recover today's loss" logic: when the budget is spent, the day is over

## Compliance note

Polymarket geo-blocks several jurisdictions (Italy included). Operating
through a blocked region risks account restriction and frozen funds.
That risk is yours and no engineering mitigates it.

## Next

- [Paper / DRY_RUN](paper-trading.md)
- [Architecture](architecture.md)
- [Strategies](strategies.md)
- [Limitations](limitations.md)
- [Offline review](analyst-prompt.md) — LLM stays outside the execution path
