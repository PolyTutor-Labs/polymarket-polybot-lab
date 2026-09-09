# Paper trading / DRY_RUN

**DRY_RUN first.** This lab is a paper-trading classroom. Simulated
sessions exist so developers can learn the engine. They are not a
countdown to depositing funds.

`DRY_RUN` defaults to `true` in `src/config.py`. That is the supported
mode.

## Why paper mode exists

Live CLOB trading needs a signing key, exchange allowances, an honest
host, and a working reconciler. Several of those pieces are unfinished
or high risk (see [limitations.md](limitations.md) and
[SECURITY.md](../SECURITY.md)).

Paper mode lets you:

- read the tick path without holding a funded wallet
- watch pair, maker, and directional experiments emit signals
- see the risk gate deny or halt
- persist orders, fills, and settlements in local SQLite
- run the offline analyst prompt against a store you created

It does **not** prove that a strategy would have made money live.

## How the simulation helps learning

`DryRunExecutor` in `src/executor.py` is the default executor
(`build_executor` logs `Executor: DRY_RUN simulation`).

**Taker `submit()`**

- Fills only as a buy.
- Requires the observed ask to be at or below the order's limit.
- Fills at the **ask**, up to **displayed** size, never assuming price
  improvement.
- Applies the same taker fee model the strategies use.
- Rejects duplicate `client_id`s (idempotency).

**Maker `place_resting()` / `poll_resting()`**

- Post-only: a bid that would cross the ask is rejected.
- A resting buy fills only when the observed best ask crosses down to
  the bid **and** displayed size covers the **full** order.
- Partial maker fills are not simulated (they would desynchronize pair
  legs in the paper model). Live GTC orders can partially fill.

The books and the BTC spot ticker are **real public market data**. The
fills are **not**. That combination is useful: you study live microstructure
with a pessimistic fill model, then compare your intuition to what the
store recorded.

## How to run a paper session

From [getting-started.md](getting-started.md):

```bash
cp .env.example .env
set -a; source .env; set +a    # load_settings() does not read .env
# leave DRY_RUN=true (the default)
python bot.py run
python bot.py status
```

SQLite state lands at `DB_PATH` (default `polybot.sqlite3`) under
`POLYBOT_DATA_DIR` or the repository root. The database is gitignored.

After a session, [analyst-prompt.md](analyst-prompt.md) is a read-only
review. The LLM stays outside the execution path.

Stay on DRY_RUN. Weeks of simulated trades are for **learning**, not a
go-live checklist.

## Differences from live trading

| Topic | DRY_RUN / paper | Live (unsupported in this lab) |
|---|---|---|
| Default | `DRY_RUN=true` | Requires `DRY_RUN=false` **and** `LIVE_TRADING_ACK=I_UNDERSTAND_THE_RISKS` |
| Executor | `DryRunExecutor` | `LiveClobExecutor` (lazy `py-clob-client` import) |
| Fills | Pessimistic, displayed size, no queue | Exchange matching; partial GTC possible |
| Key | Not required | `PRIVATE_KEY` held in-process |
| Reconciler | Skips exchange compare (`remote is None`) | `NotImplementedError` |
| Approvals | `approve` is a no-op when dry | Stub still exits 1 |
| Bankroll | Configured number | Would sync down to wallet balance if live ran |
| Accounting | Binance window open/close proxy | Official resolution + exchange positions (not wired) |

Paper results will not match live results even if someone later completes
the deferred live work. Queue position, latency, cancel/replace, stale
allowances, and adverse selection are enough to break any naive
transfer.

## What paper mode cannot teach

- Being first to a mispriced ask
- Maker queue priority
- Partial fills on one pair leg
- Host or key compromise
- On-chain allowance mistakes
- Official market resolution vs Binance spot sampled at the boundary

Treat those as [limitations](limitations.md), not as "the sim is
conservative so live will be better."

## Live mode (read-only; do not use)

The live path remains in the tree so students can **read** the dual
ack gate and the executor adapter. It is **not** a supported exercise.

- Signing key in-process; `CLOB_HOST` is not allowlisted
- Live reconciler unimplemented
- `python bot.py approve` unfinished
- `py-clob-client` / `web3` commented and unpinned

See [SECURITY.md](../SECURITY.md). If you only remember one sentence:
**DRY_RUN first.**
