# PolyTutor — Polymarket BTC 5-Minute Engine Lab

Educational research lab around a **deterministic Polymarket BTC 5-minute
Up/Down engine**. Pair arbitrage, maker quoting, and directional experiments
share one tick path. Paper / `DRY_RUN` is the default.

**No LLM in the execution path.** The agent's job (Hermes / Claude Code) is to
build, audit, and tune this code offline — see [`docs/analyst-prompt.md`](docs/analyst-prompt.md).

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

This is **not** a production trading platform, **not** a guaranteed-profit
bot, and **not** a live trading product. Design goal remains **capital
preservation first**: no single UTC day can lose more than
`MAX_DAILY_LOSS_PCT` of the bankroll (default **1%**), even counting open
positions at their worst case, even across process restarts.

## Learning path

| Doc | Why |
|---|---|
| [docs/getting-started.md](docs/getting-started.md) | Install, DRY_RUN, live-mode warnings |
| [docs/architecture.md](docs/architecture.md) | Tick path, module map, capital-protection invariants |
| [docs/analyst-prompt.md](docs/analyst-prompt.md) | Nightly read-only review prompt |
| [SECURITY.md](SECURITY.md) | Public-release hardening notes (secrets, live risk, CI) |
| [SECURITY_AUDIT.md](SECURITY_AUDIT.md) | Pre-PolyTutor security inventory (findings unchanged) |
| [strategies/README.md](strategies/README.md) | Pair arb, maker, directional experiments |

## Repository layout

```
.
├── README.md                 # this file — identity and navigation
├── SECURITY.md               # public-release hardening notes
├── SECURITY_AUDIT.md         # historical audit record (stays at repo root)
├── bot.py                    # CLI: run / status / reset / approve
├── docs/                     # getting started, architecture, analyst prompt
├── src/                      # BTC 5-minute engine (CLOB, risk, paper exec)
├── strategies/               # pair arb + maker + directional experiments
├── scripts/security/         # secret scanner (no deploy pipelines)
├── tests/                    # failure-mode suite
├── .env.example              # safety and strategy knobs (placeholders)
├── requirements.txt
└── LICENSE                   # Apache 2.0
```

Empty `config/`, `data/`, and `examples/` directories are intentionally
absent — there is no content for them yet.

## Quick start (DRY_RUN)

```bash
pip install -r requirements.txt
cp .env.example .env          # placeholders only; loader reads os.environ
set -a; source .env; set +a   # required — .env is not auto-loaded
python -m pytest tests/ -q    # all tests must pass
python scripts/security/check_secrets.py
python bot.py run             # paper-trades the live order books
python bot.py status          # PnL, budget left, streak, halt state
```

Full install notes, live-mode warnings, and emergency stop:
[docs/getting-started.md](docs/getting-started.md).

Architecture diagram and per-module responsibilities:
[docs/architecture.md](docs/architecture.md).

**Emergency stop:** `touch KILL_SWITCH` at the repository root — next
risk-gate check halts the engine. Restart requires removing the file,
`python bot.py reset`, and a human review of the halt reason.

## License

Apache 2.0 — see `LICENSE`.

## Compliance note

Polymarket geo-blocks several jurisdictions (Italy included). Operating
through a blocked region risks account restriction and frozen funds.
That risk is yours and no engineering mitigates it.
