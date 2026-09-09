# Documentation

Learning path for this Polymarket BTC 5-minute research lab.

This repository is an **educational paper-trading / DRY_RUN lab**. It is not
a production trading platform, not a guaranteed-profit bot, and not a live
trading product.

## Start here

1. [Getting started](getting-started.md) — install, DRY_RUN paper trading, live-mode warnings
2. [Architecture](architecture.md) — BTC 5-minute engine, risk gate, CLOB path
3. [Offline analyst prompt](analyst-prompt.md) — nightly read-only review (Hermes / Claude Code)
4. [Security audit](../SECURITY_AUDIT.md) — pre-PolyTutor inventory (historical; paths noted)

## Repository map

| Path | What it is |
|---|---|
| `src/` | BTC 5-minute engine: clock, CLOB/spot feeds, fees, sizing, risk gate, executor, store |
| `strategies/` | Pair-cost arbitrage, maker pair quoting, directional DRY_RUN data collection |
| `tests/` | Failure-mode tests (fees, risk, settlement, maker one-sided fills) |
| `bot.py` | CLI: `run` / `status` / `reset` / `approve` (imports and data paths resolve from the repo root; cwd-independent) |
| `.env.example` | Thresholds and safety flags (copy to `.env`; do not commit secrets) |

## Research identity

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

Live trading remains gated and out of scope until the High findings in
`SECURITY_AUDIT.md` are addressed in a later phase.
