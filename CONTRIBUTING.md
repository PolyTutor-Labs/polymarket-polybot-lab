# Contributing

This repository is an **educational research lab** around a
Polymarket BTC 5-minute engine:

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

Contributions that help people **learn the engine** are welcome.
Contributions that market it as a live product, a profitable bot, or a
source of guaranteed returns are not.

Canonical identity and disclaimer: [`README.md`](README.md) and
[`DISCLAIMER.md`](DISCLAIMER.md).

## Before you start

1. Stay on paper / `DRY_RUN` unless a later, separately scoped change
   addresses the deferred live-safety items in
   [`docs/limitations.md`](docs/limitations.md).
2. Do not change trading logic, strategies, algorithms, or execution
   behavior in a documentation or hygiene pull request.
3. Do not implement live trading, wire `approve`, pin unreviewed
   clients, or "fix" deferred bugs as drive-by work.
4. Keep strategy identifiers (`pair_cost_arb`, `brownian_dir`,
   `pair_cost_maker`) stable — the store and the offline analyst key off
   those names.
5. Preserve attribution to the original PolyBot project
   ([simoneatzori/Polybot-](https://github.com/simoneatzori/Polybot-))
   and the Apache 2.0 license. See [`NOTICE`](NOTICE).

## Local checks

From the repository root:

```bash
pip install -r requirements.txt
python -m compileall .
python -m pytest tests/ -q
python scripts/security/check_secrets.py
python scripts/quality/check.py
```

Run `python scripts/quality/check.py` before opening a pull request.
Quality CI is read-only (compile, tests, secret scan, internal links).
It does not deploy or trade.

## Pull requests

- One focused change set
- Describe the educational purpose; do not claim live performance
- Link related docs only when you change a documented path or command
- Never include `.env` files, keys, tokens, SQLite stores, or logs

Learning path for reviewers: [`docs/README.md`](docs/README.md).
Security reporting: [`SECURITY.md`](SECURITY.md).
