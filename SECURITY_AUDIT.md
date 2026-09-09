# SECURITY_AUDIT.md — Pre-PolyTutor Audit

**Repository:** https://github.com/simoneatzori/Polybot-  
**Audit clone path:** `/workspace/polytutor-labs/polybot-audit`  
**Local audit branch:** `security/polybot-audit` (not pushed)  
**Upstream HEAD audited:** `2d38982` (`origin/main`)  
**Future target (not created):** `PolyTutor-Labs/polymarket-polybot-lab`  
**Audit date:** 2026-09-09 (America/New_York)  
**Auditor scope:** PRE-POLYTUTOR SECURITY AUDIT ONLY — inventory, secrets, malware, CI/CD, dependencies, data, environment. No source rewrites, no dependency upgrades, no history rewrite, no PolyTutor-Labs repo creation.

---

## Executive summary

PolyBot is a **deterministic Polymarket BTC 5-minute trading engine** (pair arb + maker quotes + directional data-collection) with capital-protection controls, `DRY_RUN` by default, and an explicit live-mode ack gate. The tree is small (~4k LOC of Python + tests), Apache-2.0 licensed, and contains **no committed real secrets, no binaries, and no malware indicators**.

**Overall risk:** **MEDIUM** for educational / DRY_RUN lab use; **HIGH** if students or operators enable live trading without pinning/auditing `py-clob-client`, wiring reconciliation/approvals, and isolating wallet keys.

**Approved for PolyTutor transformation: YES**

Rationale: clean of planted secrets and hostile code; original capital-protection identity should be preserved; transform as a **paper-trading / architecture lab** first. Live-trading paths must remain clearly gated and documented as out-of-scope (or advanced, risk-accepted) until High findings below are addressed in a later phase.

---

## 1. Repository inventory

| Item | Detail |
|---|---|
| Language | Python 3 (stdlib + pydantic; pytest for tests) |
| Layout | Flat package at repo root + `tests/` |
| Entrypoint | `bot.py` (`run` / `status` / `reset` / `approve`) |
| Core modules | `engine.py`, `executor.py`, `maker.py`, `risk_gate.py`, `strategy.py`, `store.py`, `feeds.py`, `config.py`, `notifier.py`, `reconciler.py`, `sizing.py`, `fees.py`, `models.py`, `calibration.py`, `timeutil.py` |
| Config samples | `.env.example`, `.gitignore` |
| Docs | `README.md`, `ANALYST_PROMPT.md`, `LICENSE` (Apache-2.0) |
| Tests | `tests/test_core.py`, `test_engine.py`, `test_maker.py`, `test_risk_protection.py` |
| CI/CD | **None** (no `.github/`, no GitLab/Jenkins/Docker/Makefile) |
| Binaries / wheels / native libs | **None** observed in working tree |
| Approx size | ~26 tracked files; ~3960 lines total (including docs/tests) |
| Git history (main) | `0ca7e5b` Initial → `f7cc1b9` Import PolyBot → `2d38982` Mermaid diagram |
| Extra remote branch (not on main) | `origin/claude/claude-md-documentation-kcqmqt` @ `2dd5895` adds `CLAUDE.md` only — reviewed for secrets; **not present** in audited `main` checkout |

Identity note: this is a **specialized Polymarket BTC 5-min engine**, not a generic chatbot. Preserve that architecture in any PolyTutor lab materials.

---

## 2. Secret search

**Policy followed:** no secret values printed in this report.

### Committed secret material

| Finding | Path | Severity | Remediation |
|---|---|---|---|
| No real `.env` committed | (absent from `git ls-files`) | — | Keep `.env` gitignored; never force-add |
| `.env.example` placeholders only (empty `PRIVATE_KEY`, `TELEGRAM_*`, etc.) | `.env.example` | Info | Safe to publish; keep values empty |
| Synthetic private-key **fixture** in unit tests (`0x` + repeated hex `a`) | `tests/test_core.py` | Low | Keep synthetic; do not replace with real keys; optional comment that value is non-custodial test data |
| Settings fields marked `repr=False` for key/token | `config.py` | Positive control | Retain |
| Notifier redacts hex keys and Telegram bot-token shapes | `notifier.py` | Positive control | Retain; extend if new secret formats appear |
| Git history for `.env` / `*.pem` / `*.key` | history review | Info | Only `.env.example` introduced in import commit; **no evidence of real key material in history** |

### Secret-handling design notes (not committed leaks)

| Finding | Path | Severity | Remediation |
|---|---|---|---|
| Live executor passes `private_key` into third-party `ClobClient` and derives API creds | `executor.py` (`LiveClobExecutor._build_client`) | High (live only) | Pin + audit `py-clob-client`; dedicated low-balance wallet; never log settings; prefer OS secret store / env injection at runtime |
| Telegram bot token placed in HTTPS URL path | `notifier.py` | Medium | Prefer header-based send if API allows; ensure proxies/access logs do not retain full URLs; rotate token if leaked |
| Docstring claims load from `.env` file but `load_settings()` reads `os.environ` only (no `python-dotenv`) | `config.py` | Medium (ops) | Document required export/`set -a; source .env` pattern, or add explicit dotenv load later — do not leave mismatch that causes operators to leave secrets in unexpected places |

**No Critical committed secrets found.**

---

## 3. Malicious code review

| Check | Result |
|---|---|
| `eval` / `exec` / `pickle` / `subprocess` / `os.system` / `ctypes` / `marshal` / `base64.b64decode` obfuscation | **Not found** |
| Wallet drain / silent transfer beyond intended CLOB trading | **Not found** — live path only signs/posts Polymarket CLOB orders via `py-clob-client` after ack + key checks |
| Obfuscated payloads / packed binaries | **Not found** |
| Unexpected exfil endpoints | Outbound hosts observed: `clob.polymarket.com` (default), `api.binance.com`, `api.telegram.org`; Binance WS mentioned in comment only |
| Hidden reverse shells / miners / keyloggers | **Not found** |
| `approve` command | Stub that exits with instructions — does **not** broadcast approvals yet (`bot.py`) |

**Verdict:** No malware / hostile wallet-theft code identified in audited tree. Residual risk is **intended live trading power** once `DRY_RUN=false` + ack + key + (future) client install.

---

## 4. CI/CD review

| Item | Status | Severity | Remediation |
|---|---|---|---|
| GitHub Actions / other pipelines | Absent | Medium | Before public lab: add CI for `pytest`, lint, and secret scanning (e.g. gitleaks) on PRs |
| Deploy keys / cloud credentials in workflows | N/A | — | — |
| Unpinned Actions | N/A | — | — |
| Branch protection | Unknown (upstream hosting); no local CI config | Low | Configure on PolyTutor-Labs org when repo is created later |

---

## 5. Dependency review (no upgrades performed)

| Package | Constraint | Notes | Severity |
|---|---|---|---|
| `pydantic` | `>=2.5,<3` | Range, not fully pinned | Medium (supply chain) |
| `pytest` | `>=8` | Dev/test; unpinned minor/patch | Low–Medium |
| `py-clob-client` | Commented placeholder | **Required for live**; README says audit+pin first | **High** if live enabled without pin/audit |
| `web3` | Commented placeholder | For allowance approvals | High if live approvals wired without pin/audit |
| Lockfile (`requirements.lock` / poetry.lock / uv.lock) | **Absent** | Reproducible installs not guaranteed | Medium |

No dependency upgrades or installs were performed during this audit.

---

## 6. Data review — SAFE vs REMOVE BEFORE PUBLIC RELEASE

### SAFE to carry into a public PolyTutor lab (after attribution / license retained)

- All `*.py` source modules listed in inventory  
- `tests/**` (synthetic fixtures only)  
- `.env.example` (empty secrets)  
- `.gitignore`, `README.md`, `ANALYST_PROMPT.md`, `LICENSE`  
- This `SECURITY_AUDIT.md`

### REMOVE / NEVER PUBLISH (operator runtime artifacts — none present in clone)

| Artifact | Why |
|---|---|
| `.env` / `.env.local` / any filled env file | Wallet key, Telegram token, live ack |
| `*.sqlite3` (+ WAL/SHM/journal) | Order/fill/PnL/halt state — trading PII/operational history |
| `*.log` | May contain market/order details; token-in-URL risk if logging HTTP |
| `KILL_SWITCH` file | Ops signal only; harmless alone but indicates live ops layout |
| Any real private keys, API creds, Safe addresses with funds | Custodial risk |
| Local venv / `__pycache__` | Not source of truth |

**Clone status:** no `.env`, no sqlite DB, no logs, no pem/key files in the working tree.

### Optional remote content

- `CLAUDE.md` on remote branch `claude/claude-md-documentation-kcqmqt`: documentation only; no secret values observed in keyword scan. Not required for Phase 1 lab; include only if desired for AI-assistant workflow notes.

---

## 7. Environment review

| Variable / control | Role | Risk notes |
|---|---|---|
| `PRIVATE_KEY` | Wallet signing for live CLOB | Critical confidentiality; `repr=False`; required only when live |
| `SAFE_ADDRESS` | Polymarket Safe/proxy funder; pairs with `signature_type=2` | Misconfiguration can produce unintended order authority |
| `CLOB_HOST` | Exchange API base (default official host) | **Allowlist recommended** — arbitrary host + live key = malicious endpoint risk |
| `DRY_RUN` | Default `true` | Must stay default for labs |
| `LIVE_TRADING_ACK` | Must equal `I_UNDERSTAND_THE_RISKS` | Dual control with `DRY_RUN` |
| `KILL_SWITCH_FILE` | File presence halts new risk | Local FS control only |
| `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` | Alerts only | Token secrecy; redaction present |
| `DB_PATH` | SQLite store path | Keep out of git; path traversal less concern (local path) |
| Strategy/risk knobs (`BANKROLL`, `MAX_*`, maker timers, etc.) | Economic limits | Validators cap Kelly and daily loss % |

Network egress (runtime): Binance spot REST, Polymarket CLOB REST, optional Telegram HTTPS.

---

## 8. Findings summary (by severity)

### Critical

_None._

### High

1. **Live trading + unpinned optional client** — Enabling live requires installing `py-clob-client` / possibly `web3` without a locked audited version today (`requirements.txt`, `executor.py`, README).  
   **Remediation:** Treat live as blocked for PolyTutor Phase 1; later pin hashes/versions after third-party audit.

2. **Live reconciler not implemented** — `reconciler.py` raises `NotImplementedError` for exchange positions; README calls this a P1 launch blocker. Live without reconciliation risks undetected position drift.  
   **Remediation:** Keep live disabled in lab; implement before any live curriculum.

3. **Private key in-process for live orders** — Expected for signing, but high blast radius if host compromised or `CLOB_HOST` pointed at attacker infrastructure.  
   **Remediation:** Dedicated dust wallet, host allowlist, runtime secret injection, no agent-readable key files (as README already warns).

### Medium

4. **No CI/CD or automated secret/dependency scanning.**  
5. **Unpinned / ranged core deps; no lockfile.**  
6. **Telegram token in URL path** — log/proxy leakage risk (`notifier.py`).  
7. **`.env` documentation vs loader mismatch** (`config.py` docstring / README `cp .env.example .env` vs `os.environ` only).  
8. **Integrity bug (non-malicious):** `engine.py` calls `store.fills_for_order` but `store.py` defines `fill_for_order` — breaks state restore / settlement paths when hit (AttributeError). Flag for later fix; **not fixed in this audit.**  
9. **`bot.py approve` unfinished** — live allowance path incomplete (fails closed with exit 1).

### Low / Informational

10. Synthetic test private-key pattern in `tests/test_core.py`.  
11. SQLite unencrypted at rest (expected for local lab; do not publish DBs).  
12. Broad `except Exception` in main loop / feeds — availability/visibility, not RCE.  
13. Extra remote `CLAUDE.md` branch — docs only.  
14. Compliance note in README (geo-restrictions) — legal/ops, not code vuln.

---

## 9. Positive security controls observed

- `DRY_RUN` default + dual live ack phrase  
- Kelly and daily-loss percentage hard caps in validators  
- Risk gate deny-by-default; kill-switch file; persisted halt in SQLite  
- Secret fields `repr=False`; Telegram outbound redaction  
- Idempotent order client IDs; crash path cancels open live orders when implemented executor present  
- `.gitignore` covers `.env*`, sqlite, logs, `KILL_SWITCH`  
- No LLM on the execution path (reduces prompt-injection → trade risk)  
- Lazy import of live trading client so tests run without it  

---

## 10. PolyTutor transformation guidance (non-blocking notes)

- Preserve original PolyBot identity (BTC 5-min, risk gate, maker/arb) — do **not** force a generic bot template.  
- Phase 1 lab should emphasize **DRY_RUN**, architecture, fee/risk math, and tests.  
- Defer live wallet exercises until High items are closed.  
- Do not create `PolyTutor-Labs/polymarket-polybot-lab` as part of this audit (per brief).  

---

## 11. Audit limitations / blockers

| Item | Impact |
|---|---|
| No dependency install / vulnerability DB scan of resolved trees | Supply-chain CVEs not exhaustively enumerated |
| No dynamic runtime / network capture | Behavior inferred from static review |
| Upstream `main` only fully tree-audited; remote `CLAUDE.md` branch scanned for secrets via `git show` | Sufficient for Phase 1 |
| Auto-review intermittently rejected some parallel shell probes | Mitigated by re-running narrower commands + full file reads; **did not block** completing the audit |

**Anything blocked the audit?** No — audit completed; residual tooling friction only.

---

## 12. Approval

**Approved for PolyTutor transformation: YES**

**Overall risk:** MEDIUM (DRY_RUN / educational); HIGH if live trading enabled without further controls.

---

*End of pre-PolyTutor security audit. STOP after audit — no source fixes, no upstream push, no target repo creation.*
