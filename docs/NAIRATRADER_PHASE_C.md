# Phase C — NairaTrader preparation

## Current target

Prepare the Trading_bot for a future NairaTrader MT5 account without enabling live trading.

NairaTrader's 31 August 2026 "Trade Everything Tradable" announcement says its new account group supports crypto, indices, stocks, energies and forex from one account, and says it uses the same drawdown/scalping rule as the Disciplined Traders' Challenge. The exact account terms must be checked again before activation.

## Current implementation

- MT5 remains the execution layer.
- The NairaTrader profile is disabled by default.
- Execution remains demo-only.
- The bot must trade only symbols actually available on the connected MT5 account.
- A 5% account drawdown ceiling is represented as a safety target for the profile; the bot must not be considered compliant until the exact NairaTrader account rules are verified and the enforcement is tested.
- Live execution cannot be enabled automatically.

## Before connecting a NairaTrader account

1. Identify the exact NairaTrader program/account.
2. Verify the current trading rules for that specific account.
3. Verify whether automated/EAs are permitted under those terms.
4. Verify the MT5 broker/server and exact symbol names.
5. Connect a demo account first where available.
6. Run the bot in dry-run/demo mode.
7. Test drawdown, position sizing, stop-loss, take-profit and shutdown behavior.
8. Only after those checks should live-account compatibility be considered.

## Important

No NairaTrader credentials belong in GitHub. Store broker credentials only in local environment variables or the eventual cloud provider's encrypted secrets.
