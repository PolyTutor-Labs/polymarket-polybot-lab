# Security — educational research lab

This repository is a **Polymarket BTC 5-minute engine lab** for paper /
`DRY_RUN` research. It is **not** a production trading service, **not** a
guaranteed-profit bot, **not** financial advice, and **not** a live
trading product.

The historical inventory is in [`SECURITY_AUDIT.md`](SECURITY_AUDIT.md)
(pre-PolyTutor; findings left as written). This file is the public-release
hardening note. Task 8 documents residual risk; it does **not** implement
live trading, pin third-party clients, or add deploy pipelines.

## Report a vulnerability

Do not open a public issue that includes keys, tokens, `.env` contents,
or wallet seed material.

Prefer a private GitHub security advisory on this repository. Rotate any
exposed credential before writing it down anywhere.

## Secrets

| Rule | Detail |
|---|---|
| Never commit `.env` | Gitignored. `.env.example` is placeholders only. |
| Loader does not read `.env` | `load_settings()` in `src/config.py` reads `os.environ` only. Export vars or `set -a; source .env; set +a`. |
| Do not log settings | `PRIVATE_KEY` and `TELEGRAM_BOT_TOKEN` use `repr=False`. Do not `print` / log `model_dump()`. |
| Runtime injection | Put the live signing key in the process environment at start. Do not leave it in a file an agent or chat can read. |
| Scan before push | `python scripts/security/check_secrets.py` (fails on value-shaped findings; never prints values). |

Synthetic test keys (`0x` + a repeated hex nibble) in `tests/` are
non-custodial fixtures, not wallets.

## Live trading (high risk — out of scope for this lab)

The educational live path is still in the tree so students can *read* it.
It is **not** ready to run with funds.

| Topic | Status | Risk |
|---|---|---|
| `PRIVATE_KEY` in-process | Required to sign CLOB orders (`LiveClobExecutor._build_client`) | High blast radius if the host or `CLOB_HOST` is hostile. Dedicated dust wallet only. |
| `CLOB_HOST` | Defaults to `https://clob.polymarket.com`. Any URL is accepted. | Unofficial host + live key = signed requests to attacker infrastructure. Do not change the default for live experiments. |
| Live reconciler | `Reconciler.exchange_open_positions` raises `NotImplementedError` when `dry_run` is false | Incomplete component. Live without reconciliation can miss position drift. **Do not implement here; not production-ready.** |
| `python bot.py approve` | Stub; exits 1 | Allowance path unfinished (fails closed). |
| `py-clob-client` / `web3` | Commented placeholders in `requirements.txt` | Do not install unpinned for live. Audit and pin later; this task does not upgrade deps. |
| Dual gate | `DRY_RUN` default true + `LIVE_TRADING_ACK=I_UNDERSTAND_THE_RISKS` | Keep both. Either one alone refuses live start. |

`DRY_RUN` paper research is the supported mode.

## Telegram

`TELEGRAM_BOT_TOKEN` comes from the environment. The Bot API requires the
token in the HTTPS URL path (`/bot<token>/sendMessage`). That is a
Telegram protocol constraint, not a hardcoded credential.

Outbound text is redacted (hex keys + bot-token shapes). Send failures
run through the same redaction so `urllib` errors cannot log the URL
token. Proxies and access logs on the operator's host can still see the
path — treat the token as confidential and rotate if leaked.

## Environment variables vs loader

`src/config.py` `load_settings()` maps the knobs listed in `.env.example`
except as noted:

| Name | Loaded? |
|---|---|
| `PRIVATE_KEY`, `SAFE_ADDRESS`, `CLOB_HOST` | Yes |
| `DRY_RUN`, `LIVE_TRADING_ACK`, `KILL_SWITCH_FILE` | Yes |
| Strategy / maker / sizing / breaker knobs in `.env.example` | Yes |
| `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `DB_PATH` | Yes |
| `POLYBOT_DATA_DIR` | Yes, but only for path resolution (`data_dir` / `resolve_data_path`), not as a `Settings` field |
| `chain_id`, `window_seconds`, `market_slug_template`, `tick_size`, `min_order_size` | Code defaults only — **not** read from the environment |
| `log_level` | Settings default only; `bot.py` hardcodes `INFO` |

Empty values in `.env.example` stay empty. Do not paste real credentials.

## CI / CD

Educational quality CI lives in [`.github/workflows/quality.yml`](.github/workflows/quality.yml).
It is **not** a deploy pipeline and **not** live-trading automation.

| Rule | Detail |
|---|---|
| Permissions | `contents: read` only (workflow and job). No write, no `pull-requests`, no packages. |
| Third-party actions | Pinned by commit digest (`actions/checkout` v4.4.0, `actions/setup-python` v5.6.0). |
| Jobs | `compileall`, `pytest tests/`, `scripts/security/check_secrets.py`, internal markdown-link check. |
| Not present | Deploy, publish, live `bot.py run`, secret echo, `contents: write`. |

Run the same gates locally:

```bash
python -m compileall .
python -m pytest tests/ -q
python scripts/security/check_secrets.py
python scripts/quality/check.py          # all of the above plus syntax + doc links
```

Checkout uses `persist-credentials: false`. Do not add write permission
unless a later documented job requires it.

## Dependencies

| Package | Constraint | Note |
|---|---|---|
| `pydantic` | `>=2.5,<3` | Ranged; no lockfile. Acceptable for the paper lab. |
| `pytest` | `>=8` | Test-only. |
| `py-clob-client` | Commented | Live-only. Do not uncomment without audit + exact pin. |
| `web3` | Commented | Future approvals only. Same pin/audit rule. |

No lockfile. Supply-chain risk is **documented**, not “fixed” by unreviewed
upgrades. Do not treat `pip install -r requirements.txt` as a production
bill of materials.

## What this hardening does not do

Deferred on purpose (do not treat as a launch checklist):

- Live reconciler implementation
- `approve` wiring to chain
- Full live safety architecture / `CLOB_HOST` allowlist enforcement
- Dependency pinning / upgrades
- Deploy pipelines or live-trading automation (quality CI only)

Trading logic, strategies, algorithms, and risk-gate behavior are unchanged.
