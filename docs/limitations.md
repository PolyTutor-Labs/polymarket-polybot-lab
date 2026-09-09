# Known limitations

This lab is an educational engine. The items below are **deferred on
purpose**. Task 10 documents them. It does **not** fix them.

Do not treat this page as a launch checklist.

## Deferred engineering items

### Live reconciler incomplete

`Reconciler.exchange_open_positions()` in `src/reconciler.py` returns
`None` in dry-run (skip compare) and raises `NotImplementedError` when
`dry_run` is false.

The module comments call reconciliation a P1 launch blocker. Live
trading without an exchange position check can miss drift between the
SQLite store and the CLOB. **Do not implement it in a documentation
change. Not production-ready.**

### `fills_for_order` / `fill_for_order` mismatch

The pre-PolyTutor [SECURITY_AUDIT.md](../SECURITY_AUDIT.md) flagged a
Medium integrity finding: engine restore/settlement calling
`fills_for_order` while `src/store.py` exposes `fill_for_order`.

In the current tree the store method is `fill_for_order` (aggregates
fills for one `client_id`). This item **stays on the deferred list**.
Do not assume settlement restore is proven-correct for live use. Do not
"fix" the lookup, rename APIs, or change settlement behavior as part of
documentation work.

### `approve` stub

`python bot.py approve` is unfinished:

- In `DRY_RUN` it prints that approvals are live-only and returns.
- In live mode it prints instructions and **`raise SystemExit(1)`**.

It does not broadcast USDC (ERC-20) or CTF (ERC-1155) allowances.
Fails closed. Wiring it requires audited contract addresses and a pinned
`web3` stack — later work, not this lab phase.

### Dependency pinning

`requirements.txt` installs `pydantic` (`>=2.5,<3`) and `pytest`
(`>=8`) only. There is no lockfile.

`py-clob-client` and `web3` are **commented placeholders**. Uncommenting
them without an audit and an exact pin is a High finding in the security
audit. This task does not upgrade or pin dependencies.

### Full live safety work

Still out of scope:

- `CLOB_HOST` allowlist enforcement (any URL is accepted today)
- Removing or isolating the in-process `PRIVATE_KEY` for live signing
- Complete live crash-recovery / cancel-all curriculum
- Deploy pipelines or live-trading automation (quality CI is read-only)

See [SECURITY.md](../SECURITY.md).

## Paper-accounting limitations (accepted)

These are design limits of the educational sim, not tickets to "fix"
into a production exchange:

| Limit | Why it matters for learning |
|---|---|
| Window open/close from Binance spot at the boundary | Official resolution may differ; paper PnL is an approximation |
| Flat close (`close == open`) treated as DOWN | Confirm per-market tie rules before trusting any accounting |
| DRY_RUN taker fills: displayed size, no improvement | Optimistic live fills will not appear in the sim |
| DRY_RUN maker fills: all-or-nothing | Live GTC can partially fill and desynchronize legs |
| No queue / no "quoted against" model | Maker experiments understate selection |
| REST spot/book polls, 5s stale window | Not a production latency path (comments mention WS as a future swap) |

## Strategy limitations (research, not products)

Documented fully in [strategies.md](strategies.md):

- Pair-cost arb is a **concept**. Race latency and unhedged legs dominate
  any textbook "buy both under 1" story.
- Maker pair quoting adds one-sided-fill risk; the hedge path can still
  end in `hold` / `unhedged`.
- Directional Brownian/EWMA is **known-wrong** (fat tails, lagging vol)
  and is DRY_RUN data collection only.

No experiment is claimed profitable, production-ready, or validated live.

## Security leftovers (not re-opened here)

From the historical audit, still relevant for readers:

- Medium: Telegram bot token in the HTTPS URL path (protocol constraint;
  send failures are redacted)
- Medium: `.env` file vs `load_settings()` reading `os.environ` only
  (documented; export or `set -a; source .env`)
- Low: SQLite unencrypted at rest — do not publish `*.sqlite3`
- Info: synthetic test keys in `tests/` are fixtures, not wallets

Findings remain as written in [SECURITY_AUDIT.md](../SECURITY_AUDIT.md).

## What this repository deliberately does not do

From the original engine — still true:

- No LLM calls at trade time
- No martingale / DCA-into-losers
- No "recover today's loss" logic when the daily budget is spent
- No generic multi-market framework
- No live directional trading (`enable_directional_live` is false)

## Functional impact of the documentation task

| Area | Changed? |
|---|---|
| Trading logic | NO |
| Strategies | NO |
| Algorithms | NO |
| Dependencies | NO |
| Execution behavior | NO |
