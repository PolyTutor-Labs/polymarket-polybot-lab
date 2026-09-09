# Strategies — research experiments

These modules sit beside the BTC 5-minute engine. The engine calls them;
they do not bypass the risk gate. The hard fee gate runs **here**,
before sizing and before the risk gate.

Do not rename the identifiers (`pair_cost_arb`, `brownian_dir`,
`pair_cost_maker`). Store rows and the offline analyst prompt key off
those names.

Full educational write-up: [docs/strategies.md](../docs/strategies.md).

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

These are **historical experiments**. Nothing here is a production
strategy, a live-performance report, or a claim of profitability.

## Pair-cost arbitrage — `PairCostArb` (`pair_cost_arb`)

| | |
|---|---|
| **File** | `strategy.py` |
| **Purpose** | Taker experiment: buy YES and NO when the ask sum is under 1 after fees (`pair_cost_net_edge` ≥ `MIN_EDGE`). |
| **Educational goal** | Teach pair-cost mechanics, equal-share legs, the hard fee gate, and the unhedged-leg halt. |
| **Limitations** | Needs both asks cheap enough *and* both fills. Paper mode does not model race latency. A failed second leg halts. Not production-ready; no live performance claimed. |

## Maker pair quoting — `MakerPairQuoter` (`pair_cost_maker`)

| | |
|---|---|
| **File** | `maker.py` |
| **Purpose** | Rest passive bids on both outcomes so a two-sided fill would lock a pair-cost edge. Escalates one-sided fills: reprice → taker hedge → hold-with-alert. |
| **Educational goal** | Contrast providing two-sided prices with taking asks; study quote-time risk reservation and a small state machine. |
| **Limitations** | Dry-run maker fills are all-or-nothing and ignore queue. `MAKER_FEE_BPS` defaults to 0. Hedge can still fail (`unhedged` / `hold`). Not production-ready; no live performance claimed. |

## Directional — `BrownianDirectional` (`brownian_dir`)

| | |
|---|---|
| **File** | `strategy.py` (plus `EwmaVol`) |
| **Purpose** | DRY_RUN data collection: `P(close > open)` under driftless Brownian motion with EWMA vol; at most one side after the fee gate. |
| **Educational goal** | Show a toy probability, its known-wrong assumptions (fat tails, lagging vol), shrinkage/calibration gates, and why live directional stays off. |
| **Limitations** | Model is not Gaussian reality. Engine keeps `enable_directional_live = False`. Paper calibration is not live expectancy. Do not enable live. |

See [docs/architecture.md](../docs/architecture.md) for the tick path
and [docs/limitations.md](../docs/limitations.md) for deferred items.
