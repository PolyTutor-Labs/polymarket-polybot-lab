# Strategies — research experiments

These modules sit beside the BTC 5-minute engine. The engine calls them;
they do not place orders themselves. The hard fee gate runs **here**,
before sizing and before the risk gate.

Do not rename the strategy identifiers (`pair_cost_arb`, `brownian_dir`,
maker strategy id). Downstream store rows and the offline analyst prompt
key off those names.

| File | Experiment | Role |
|---|---|---|
| `strategy.py` | Pair-cost arbitrage | Taker: buy YES+NO when ask sum is under 1 after fees (`PairCostArb`) |
| `strategy.py` | Directional (DRY_RUN) | Brownian / EWMA-vol probability (`BrownianDirectional`) — data collection only |
| `maker.py` | Maker pair quoting | Passive two-sided quotes (`MakerPairQuoter`) with one-sided-fill escalation |

```
engine (src/)
        ↓
pair arbitrage          strategies/strategy.py
        +
maker experiments       strategies/maker.py
        +
directional experiments strategies/strategy.py
        +
paper / DRY_RUN         default executor path
```

`PairCostArb` is the only strategy with bounded downside. Directional
stays in DRY_RUN until calibration in `src/calibration.py` proves the
model. Maker quotes reserve worst-case loss at quote time.

See [docs/architecture.md](../docs/architecture.md) for the tick path.
