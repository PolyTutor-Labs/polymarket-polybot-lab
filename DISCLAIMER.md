# Disclaimer

This software is provided for **education and research** under the
Apache 2.0 license ([`LICENSE`](LICENSE); attribution in [`NOTICE`](NOTICE)).
It is offered **as is**, without warranty of any kind.

This repository is an educational Polymarket BTC 5-minute engine
research lab. It is **not**:

- a production trading platform
- a profitable trading service
- a guaranteed-profit system
- financial advice or investment advice
- a solicitation to trade
- a live trading product

## Results and risk

- Simulated or historical paper / `DRY_RUN` results do **not** predict
  live results.
- Capital-protection rules (daily loss cap, kill switch, halt on an
  unhedged pair leg) are teaching invariants, not a promise of outcomes.
- Enabling live mode can lose real funds. Live trading is incomplete
  and unsupported in this lab (see [`docs/limitations.md`](docs/limitations.md)
  and [`SECURITY.md`](SECURITY.md)).
- You are responsible for jurisdiction, account, and tax rules that
  apply to you.

## Compliance

Polymarket geo-blocks several jurisdictions (Italy included). Operating
through a blocked region risks account restriction and frozen funds.
That risk is yours; no engineering control in this repository mitigates
it.
