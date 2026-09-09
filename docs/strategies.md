# Strategies and experiments

The engine calls into `strategies/`. Strategies **do not place orders
themselves** (except the maker quoter, which still reserves risk at the
gate before any quote rests). The hard fee gate runs **inside**
strategy evaluation, before sizing and before the risk gate.

Do not rename the identifiers. Store rows and the offline analyst prompt
key off them:

| Identifier | Class | File |
|---|---|---|
| `pair_cost_arb` | `PairCostArb` | `strategies/strategy.py` |
| `brownian_dir` | `BrownianDirectional` | `strategies/strategy.py` |
| `pair_cost_maker` | `MakerPairQuoter` | `strategies/maker.py` |

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

These are **historical experiments** for study. This page does not claim
profitability, production readiness, or live performance.

Code-adjacent summary: [strategies/README.md](../strategies/README.md).

## Pair-cost arbitrage (`pair_cost_arb`)

### Purpose

`PairCostArb.evaluate()` looks at the YES and NO **asks**. If both books
have size, it computes net edge after taker fees:

```
gross = 1 - (ask_yes + ask_no)
net   = gross - fee(yes) - fee(no)
```

When `net >= MIN_EDGE`, it returns **two paired signals** (YES and NO)
at the observed asks. The engine then sizes both legs to the **same
share count** (thinner ask, `MAX_BET`, remaining daily budget).

The educational idea is mechanical: a binary pair that costs less than 1
after fees, if **both** legs fill, settles to 1 per share regardless of
direction. That is a pair-cost concept, not a statement that the engine
captures it in practice.

### Educational goal

- See a **hard fee gate** reject a "cheap" pair that is expensive after
  `rate * min(p, 1-p)` on both legs.
- See why legs must be equal shares (a size mismatch is directional).
- See the unhedged-leg halt: first fill + second fail is an incident,
  not a retry loop.

### Limitations

- Requires someone else to offer both asks cheaply enough, then requires
  the lab process to lift them before others do. Paper mode does not
  model race latency.
- A failed second leg leaves a naked binary. The engine halts; it does
  not "fix" the book.
- Window settlement in this lab uses Binance open/close proxies, not the
  market's official resolution source.
- Not documented as production-ready. Not a live-performance result.

## Maker pair quoting (`pair_cost_maker`)

### Purpose

`MakerPairQuoter` rests **passive bids on both outcomes** so that if
both fill, the sum is at most `1 - MIN_EDGE` after maker fees. Instead
of taking mispriced asks, the experiment *provides* two-sided prices and
studies two-sided flow.

The new risk is the **one-sided fill**: a trend hits only the losing
side. Containment in the existing code, in order:

1. Reserve the naked-leg worst case (full premium + fee) against the
   daily budget at **quote** time.
2. Reprice the remaining leg up to a passive hedge cap.
3. After `HEDGE_WAIT_S` (or near the cancel deadline), take the other
   side if the locked loss is at worst `HEDGE_MAX_LOSS_PER_SHARE`.
4. Otherwise cancel, hold the naked leg to settlement as `unhedged`
   (risk already reserved), and alert. No martingale, no chase.

Unfilled quotes are torn down at `QUOTE_CANCEL_REMAINING_S`, on any
halt (`go_flat`), and on restart.

### Educational goal

- Contrast taker pair-arb (race the ask) with maker pair quotes (provide
  both bids).
- Study a state machine (`idle` → `quoted` → `partial` → `hold`/`done`)
  rather than a single-shot signal.
- See why worst-case reservation must happen **before** a fill can
  occur.

### Limitations

- Dry-run maker fills are all-or-nothing and pessimistic. Live GTC
  orders can partially fill; the paper model will not teach that
  behavior.
- Queue position, cancel/replace races, and being quoted against are
  not simulated.
- `MAKER_FEE_BPS` defaults to 0 and must be checked against market
  metadata before anyone treats paper fees as realistic.
- Not production-ready. No live performance is claimed.

## Directional experiment (`brownian_dir`)

### Purpose

`BrownianDirectional` estimates `P(close > open)` under **driftless
Brownian motion** with EWMA volatility:

```
z    = log(spot / window_open) / (sigma_per_sqrt_s * sqrt(seconds_remaining))
p_up = Φ(z)
```

It then compares `p_up` (YES) and `1 - p_up` (NO) to the asks, applies
the directional fee gate, and keeps at most one side (better net edge).
`EwmaVol` tracks log-return variance per second.

The engine flag `enable_directional_live` is **False**. Directional
entries run only when `DRY_RUN` is true (or that flag is flipped in
code — it is not a supported live switch). Calibration
(`src/calibration.py`) records Brier / log loss / hit rate from
settlements that stored a predicted probability.

### Educational goal

- Implement a toy probability, then **watch it fail honestly**: 5-minute
  BTC returns are fat-tailed and autocorrelated, not Gaussian; EWMA vol
  lags regime changes.
- Learn why shrinkage toward 0.5 (`PROB_SHRINKAGE`), `MIN_PROB`,
  `DIR_MIN_ELAPSED_S`, `VOL_MIN_SAMPLES`, and `MAX_SPREAD` exist.
- Practice reading calibration stats without promoting the model to a
  live switch.

### Limitations

- The model is known-wrong by construction (see the class docstring).
- It is **data collection**, not a live strategy.
- Calibration on paper fills is not evidence of live expectancy.
- Do not enable it live. The offline analyst prompt forbids proposing
  that while calibration thresholds fail.

## Shared rules

- Fee math is in `src/fees.py`. A signal below `MIN_EDGE` after fees is
  rejected, not logged-and-sent.
- Sizing (`src/sizing.py`) may shrink a directional notional; it does
  not bypass the gate.
- The risk gate can still deny an otherwise valid signal (budget, kill
  switch, streak, drawdown, exposure).
- Identifiers stay stable so `polybot.sqlite3` rows remain readable.

## Related documents

- [Architecture](architecture.md)
- [Paper / DRY_RUN](paper-trading.md)
- [Limitations](limitations.md)
- [Offline analyst prompt](analyst-prompt.md)
