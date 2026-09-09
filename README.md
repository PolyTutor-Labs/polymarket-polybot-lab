# PolyTutor — Polymarket BTC 5-Minute Engine Lab

Educational research lab around a deterministic **Polymarket BTC 5-minute
Up/Down engine**. Pair arbitrage, maker quoting, and directional experiments
share one tick path. Paper / `DRY_RUN` is the default and the supported
mode.

```
Polymarket BTC 5-minute engine
        ↓
pair arbitrage
        +
maker experiments
        +
directional experiments
        +
paper / DRY_RUN research
```

This repository is an **educational engine** and **research lab**. It is
**not** a production trading platform, **not** a guaranteed-profit system,
**not** financial advice, and **not** a live trading service.

## Overview

The engine studies one market family: Polymarket BTC 5-minute Up/Down
windows. Each tick follows a single path:

```
Market data
    ↓
Feeds
    ↓
Engine
    ↓
Strategies
    ↓
Risk gate
    ↓
Executor
    ↓
Store
```

**No LLM sits on the execution path.** Offline review belongs in
[`docs/analyst-prompt.md`](docs/analyst-prompt.md). The lab exists so
developers can read the architecture, run paper sessions, inspect
historical experiments, and learn the engineering trade-offs — not to
operate a live product.

Capital preservation remains the original design goal: no single UTC day
is allowed to lose more than `MAX_DAILY_LOSS_PCT` of the configured
bankroll (default **1%**), counting open positions at their worst case,
even across process restarts. That rule is a teaching invariant, not a
promise of outcomes.

## Purpose

This lab helps developers understand:

- **what the engine does** — poll spot and CLOB books, evaluate
  experiments, gate risk, simulate or (gated) submit orders, persist
  state, settle expired windows
- **why the architecture exists** — one door to execution (the risk
  gate), restart-proof limits, equal-share pair legs, hard fee math
- **how experiments were designed** — pair-cost taker, two-sided maker
  quotes, Brownian / EWMA directional data collection
- **what lessons were learned** — never price from Gamma, treat fees as
  a hard gate, halt on an unhedged pair leg, keep the model off the
  hot path
- **what limitations remain** — live reconciler, approve stub, fill
  lookup integrity, dependency pinning, full live safety

Use it as a paper-trading classroom and a code-reading companion. Do not
use it as a money-making bot or investment advice.

## Repository Identity

| This lab is | This lab is not |
|---|---|
| An educational engine | A production trading platform |
| A research lab for historical experiments | A guaranteed-return system |
| A paper / `DRY_RUN` classroom | A live trading service |
| A place to study engineering lessons | Financial or investment advice |

Original identity to preserve: a specialized BTC 5-minute engine, not a
generic chatbot or multi-venue framework.

## Architecture Overview

Every candidate order takes the same path. The **risk gate is the only
door** to the executor. Nothing reaches a simulated or live book without
passing the daily worst-case budget check.

```
Binance spot + CLOB top-of-book + server-synced clock
        ↓
Engine.tick()  (entry zone, book sanity, window tracking)
        ↓
Strategies     (pair arb · maker · directional)
        ↓
Sizing         (quarter-Kelly + shrinkage; budget cap)
        ↓
Risk gate      (1%/day worst case · kill switch · streak · drawdown)
        ↓
Executor       (DryRun by default; live CLOB is gated and incomplete)
        ↓
SQLite store   (orders · fills · settlements · risk state)
        ↓
settle_expired() + reconciler (live path unimplemented)
```

Full diagram, module map, and capital-protection invariants:
[`docs/architecture.md`](docs/architecture.md).

## Engine Components

Only modules that exist in this tree:

| Component | Path | Role |
|---|---|---|
| CLI | `bot.py` | `run` / `status` / `reset` / `approve` |
| Settings | `src/config.py` | Pydantic v2; `DRY_RUN` default; live ack gate |
| Clock | `src/timeutil.py` | 5-minute windows; entry-zone rule |
| Feeds | `src/feeds.py` | Binance spot + CLOB top-of-book; stale ticks refused |
| Fees | `src/fees.py` | CLOB fee model; hard fee gate |
| Models | `src/models.py` | Window, book, order, fill, signal types |
| Engine | `src/engine.py` | Tick orchestration, pair legs, settlement |
| Sizing | `src/sizing.py` | Quarter-Kelly, shrinkage, caps |
| Risk gate | `src/risk_gate.py` | Worst-case daily budget + circuit breakers |
| Executor | `src/executor.py` | `DryRunExecutor` (default) / gated `LiveClobExecutor` |
| Store | `src/store.py` | SQLite WAL: orders, fills, settlements, risk KV |
| Reconciler | `src/reconciler.py` | Dry-run skip; **live path raises `NotImplementedError`** |
| Calibration | `src/calibration.py` | Rolling Brier / log loss / hit rate |
| Notifier | `src/notifier.py` | Optional Telegram alerts with redaction |
| Pair + directional | `strategies/strategy.py` | `PairCostArb`, `BrownianDirectional`, `EwmaVol` |
| Maker | `strategies/maker.py` | `MakerPairQuoter` (`pair_cost_maker`) |

There is no dashboard service, no deploy pipeline, and no implemented
live position reconciler.

## Strategies and Experiments

Three historical experiments sit beside the engine. They emit signals or
rest quotes; they do not bypass the risk gate.

| Experiment | Id | Kind |
|---|---|---|
| Pair-cost arbitrage | `pair_cost_arb` | Taker: buy YES+NO when the ask sum is under 1 after fees |
| Maker pair quoting | `pair_cost_maker` | Passive two-sided bids; one-sided-fill escalation |
| Directional | `brownian_dir` | Driftless Brownian / EWMA-vol — **DRY_RUN data collection** |

Each experiment has a purpose, an educational goal, and explicit
limitations. None is documented as production-ready or as a source of
live performance.

Details: [`docs/strategies.md`](docs/strategies.md) and
[`strategies/README.md`](strategies/README.md).

## DRY_RUN / Paper Trading

`DRY_RUN=true` is the default. Paper mode is how this lab is meant to be
used.

- The executor simulates fills against the **live** CLOB top-of-book
  (pessimistic: displayed size only, no price improvement, no queue
  model).
- Settings load from `os.environ` only — copy [`.env.example`](.env.example)
  and `set -a; source .env; set +a` before `python bot.py run`.
- Live mode additionally requires `LIVE_TRADING_ACK=I_UNDERSTAND_THE_RISKS`.
  Either flag alone refuses to start. Live remains **out of scope**.

Read [`docs/paper-trading.md`](docs/paper-trading.md) before the first
paper session. **DRY_RUN first.**

## Getting Started

From the repository root:

```bash
pip install -r requirements.txt
cp .env.example .env          # placeholders only; loader reads os.environ
set -a; source .env; set +a   # required — .env is not auto-loaded
python -m compileall .
python -m pytest tests/ -q
python scripts/security/check_secrets.py
python scripts/quality/check.py
python bot.py run             # paper-trades the live order books
python bot.py status          # store stats, daily PnL, halt state
```

`python bot.py` may be launched from any working directory. Imports and
runtime files resolve from the repository root via `Path(__file__)`.

Install notes, environment caveats, and emergency stop:
[`docs/getting-started.md`](docs/getting-started.md).

**Emergency stop:** `touch KILL_SWITCH` at the repository root. The next
risk-gate check halts the engine. Restart requires removing the file,
`python bot.py reset`, and a human review of the halt reason.

## Testing

Quality gates are educational. They do not deploy, trade, or talk to an
exchange on your behalf.

| Check | Command |
|---|---|
| Syntax compile | `python -m compileall .` |
| Unit tests | `python -m pytest tests/ -q` |
| Secret scan | `python scripts/security/check_secrets.py` |
| Combined gates (compile, syntax, pytest, secrets, doc links) | `python scripts/quality/check.py` |
| Markdown links only | `python scripts/quality/check.py links` |

`tests/` covers failure modes from the original review: window
boundaries, the fee gate, Kelly caps, breaker trips, idempotent client
ids, pessimistic fills, calibration math, live-mode ack, maker
one-sided-fill handling, path portability, and lab hygiene. CI
(`.github/workflows/quality.yml`) is **read-only** quality CI — not a
deploy pipeline.

## Security

Public-release notes and the historical inventory stay at the repository
root. Do not remove them.

| Document | What it is |
|---|---|
| [`SECURITY.md`](SECURITY.md) | Hardening notes for this educational lab (secrets, live risk, CI, deferred items) |
| [`SECURITY_AUDIT.md`](SECURITY_AUDIT.md) | Pre-PolyTutor security inventory (findings left as written) |

Report vulnerabilities privately. Never open a public issue that includes
keys, tokens, `.env` contents, or wallet seed material.

## Limitations

Deferred on purpose. **Documented only — not fixed in this task.**

- Live reconciler incomplete (`NotImplementedError` when `dry_run` is false)
- `fills_for_order` / `fill_for_order` integrity finding (audit Medium)
- `python bot.py approve` is a stub (exits 1)
- Dependency pinning / lockfile absent; `py-clob-client` and `web3` commented
- Full live safety work (`CLOB_HOST` allowlist, in-process key, live curriculum)

Paper accounting also approximates window open/close from Binance spot
and cannot model queue position. Details:
[`docs/limitations.md`](docs/limitations.md).

## Contributing

This is an educational research lab. Contributions that help people
**learn the engine** are welcome. Contributions that market it as a live
product or a source of guaranteed returns are not.

1. Stay on paper / `DRY_RUN` unless a later, separately scoped task
   addresses the deferred live-safety items.
2. Do not change trading logic, strategies, algorithms, or execution
   behavior in a documentation or hygiene pull request.
3. Do not implement live trading, wire `approve`, pin unreviewed
   clients, or "fix" deferred bugs as drive-by work.
4. Run `python scripts/quality/check.py` before opening a PR.
5. Keep strategy identifiers (`pair_cost_arb`, `brownian_dir`,
   `pair_cost_maker`) stable — the store and the offline analyst key off
   those names.
6. Preserve attribution to the original PolyBot project (below).

Learning path for reviewers: [`docs/README.md`](docs/README.md).

## Disclaimer

This software is provided for **education and research** under the
Apache 2.0 license ([`LICENSE`](LICENSE)). It is offered **as is**,
without warranty of any kind.

- It is **not** financial advice, investment advice, or a solicitation
  to trade.
- Simulated or historical paper results do **not** predict live results.
- Enabling live mode can lose real funds. Live trading is incomplete and
  unsupported in this lab.
- You are responsible for jurisdiction, account, and tax rules that
  apply to you.

Polymarket geo-blocks several jurisdictions (Italy included). Operating
through a blocked region risks account restriction and frozen funds.
That risk is yours; no engineering control in this repository mitigates
it.

## Attribution

### Original project

The BTC 5-minute engine, pair-arbitrage and maker experiments,
directional data-collection path, risk gate, dry-run executor, and
capital-protection invariants come from:

**[simoneatzori/Polybot-](https://github.com/simoneatzori/Polybot-)**

Licensed under Apache 2.0. That attribution must be preserved.

### PolyTutor improvements

PolyTutor-Labs did **not** rewrite the trading engine. The lab work so
far is:

| Area | What changed |
|---|---|
| Repository organization | Engine under `src/`, experiments under `strategies/`, docs under `docs/` |
| Portability | Paths resolve from the repository root, not process cwd |
| Security hardening | `SECURITY.md`, secret scanner, live-risk documentation, Telegram redaction |
| Testing | Quality gates, compile/link/secret CI, lab-hygiene tests |
| Educational documentation | This README and the `docs/` learning path (this task) |

Trading logic, strategies, algorithms, installed dependencies, and
execution behavior are unchanged by the documentation transformation.
