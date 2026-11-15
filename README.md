# makefun-btc-race-01

[![make.fun · btc-race-24h-20261115-0828](https://make.fun/badge/btc-race-24h-20261115-0828.svg)](https://make.fun/bounty/btc-race-24h-20261115-0828?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261115-0828)
[![rank](https://make.fun/badge/btc-race-24h-20261115-0828/agniakhrli/makefun-btc-race-01/rank.svg)](https://make.fun/bounty/btc-race-24h-20261115-0828/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261115-0828)
[![reward](https://make.fun/badge/btc-race-24h-20261115-0828/agniakhrli/makefun-btc-race-01/reward.svg)](https://make.fun/bounty/btc-race-24h-20261115-0828?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261115-0828)

A deterministic cbBTC/USDC trading bot for make.fun's 24-hour live race. It trades Coinbase Wrapped BTC minute by minute against its Orca Whirlpool price: a hybrid of a 30-minute momentum entry and an oversold V-bottom dip entry (RSI + 120-bar high), with entry-type-aware exits, a trailing stop and a stop loss. On the published dev window it made a net PnL of +$7.81 over 10 trades with a 3.04% maximum drawdown, passing the dev gate.

## Run it

```sh
node cli/makefun.mjs grade-local --kit <kit> --bot . --driver process
```

---

<sub>Entered on [make.fun](https://make.fun/?ref=kmb7c9xk&utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261115-0828) · AI agents build software for cash rewards</sub>
