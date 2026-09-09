# Documentation

Learning path for this Polymarket BTC 5-minute **educational research
lab**.

This repository is a paper-trading / `DRY_RUN` classroom. It is not a
production trading platform, not a guaranteed-profit system, not
financial advice, and not a live trading service.

## Start here

1. [Repository README](../README.md) — overview, identity, attribution
2. [Getting started](getting-started.md) — install, DRY_RUN, emergency stop
3. [Paper trading](paper-trading.md) — why simulation exists; **DRY_RUN first**
4. [Architecture](architecture.md) — actual tick path and module map
5. [Strategies](strategies.md) — pair arb, maker, directional experiments
6. [Limitations](limitations.md) — deferred items (documented, not fixed)
7. [Offline analyst prompt](analyst-prompt.md) — read-only nightly review
8. [Security](../SECURITY.md) — secrets, live-trading risk, CI/deps
9. [Security audit](../SECURITY_AUDIT.md) — pre-PolyTutor inventory (historical)

Code-adjacent strategy index: [strategies/README.md](../strategies/README.md).

## Repository map

| Path | What it is |
|---|---|
| `src/` | BTC 5-minute engine: clock, CLOB/spot feeds, fees, sizing, risk gate, executor, store |
| `strategies/` | Pair-cost arbitrage, maker pair quoting, directional DRY_RUN data collection |
| `tests/` | Failure-mode tests (fees, risk, settlement, maker one-sided fills) |
| `bot.py` | CLI: `run` / `status` / `reset` / `approve` (cwd-independent) |
| `.env.example` | Thresholds and safety flags (copy to `.env`; loader reads `os.environ` only) |
| `scripts/security/` | Secret scanner (`check_secrets.py`); no deploy pipelines |
| `scripts/quality/` | Local quality runner (`check.py`): compileall, pytest, secrets, doc links |
| `.github/workflows/` | Educational quality CI only (`contents: read`; no deploy) |

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
`SECURITY_AUDIT.md` are addressed in a later phase. This documentation
task does not start that work.
