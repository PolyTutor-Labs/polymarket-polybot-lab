# Changelog

All notable **lab packaging** changes for this educational research
repository are recorded here.

This project is a Polymarket BTC 5-minute engine lab (pair arbitrage,
maker experiments, directional experiments, paper / `DRY_RUN` research).
It is not a production trading platform, not a profitable trading
service, not a guaranteed-profit system, not financial advice, and not
a live trading product.

Entries describe repository, documentation, security, and test work.
They do **not** claim profitability, trading success, production
readiness, or live performance.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows [SemVer](https://semver.org/spec/v2.0.0.html) for
the public lab snapshot, not for strategy expectancy.

## [0.1.0] — 2026-09-09

First public PolyTutor lab snapshot of
[simoneatzori/Polybot-](https://github.com/simoneatzori/Polybot-).

PolyTutor-Labs did not rewrite the trading engine. Trading logic,
strategies, algorithms, and execution behavior are unchanged from the
imported engine.

### Added

- PolyTutor migration into
  [PolyTutor-Labs/polymarket-polybot-lab](https://github.com/PolyTutor-Labs/polymarket-polybot-lab)
  with original Apache 2.0 attribution preserved
- Repository organization: engine under `src/`, experiments under
  `strategies/`, learning docs under `docs/`
- Path portability: imports and runtime files resolve from the
  repository root via `Path(__file__)`, not process cwd
- `SECURITY.md` public-release notes and
  `scripts/security/check_secrets.py` (tracked files; never prints values)
- Educational quality gates: `scripts/quality/check.py`, `pytest.ini`,
  read-only CI in `.github/workflows/quality.yml`
- Educational documentation: architecture, strategies, paper trading,
  getting started, limitations, offline analyst prompt
- `CONTRIBUTING.md`, `DISCLAIMER.md`, and this changelog
- `NOTICE` separating original PolyBot authorship from PolyTutor lab
  packaging

### Changed

- README and docs reframed as an educational paper / `DRY_RUN` research
  lab (not a live trading product)
- `.gitignore` expanded for secrets, SQLite store files, and local
  artifacts
- Telegram send-failure logs redacted so URL tokens are not printed
- Environment docs aligned with `load_settings()` (`os.environ` only)

### Security

- Dual live gate kept (`DRY_RUN` default plus `LIVE_TRADING_ACK`)
- Live path documented as High risk and out of scope (unpinned client,
  unimplemented reconciler, in-process signing key)
- Quality CI uses `contents: read` only; no deploy or live-trading jobs

### Fixed

- None in trading logic, strategies, algorithms, or execution. Deferred
  engine items remain documented in [`docs/limitations.md`](docs/limitations.md).

[0.1.0]: https://github.com/PolyTutor-Labs/polymarket-polybot-lab
