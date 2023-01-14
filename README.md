# FTX Trading Bot

## Background
This is the code that I used for the FTX quant trading competition for university students. Unfortunately, it ended early due to the collapse of FTX. However, during the few days that I had it running, it returned 0.167%, traded $5,745.79 in volume, and opened 41 positions.

## Strategy
As my first ever automated trading program, I wanted to keep it simple. I used a simple moving average (SMA) mean reversion strategy that a winner in a past competition had used in FTX's "Quant Zone" feature. Instead of using FTX's Quant Zone interface, I coded it in Python. I had to adapt the strategy to be long-only on the spot market. My strategy took the SMA over the past hour using 15 minute intervals and compared it against the current price. If the current price is 0.8% below the SMA, then the strategy would market buy and place a limit sell at the SMA. The strategy's execution is in the `strategyexec.py` file.

## Monitoring
To monitor the activity of the bot, I used Discord webhooks to notify me of order fills. The fills monitor is in the `fills.py` file.

## Disclaimer
This program was put together rather sloppily as I was figuring out how the FTX API worked. The trading execution only works well in healthy market conditions. There are many things I would do differently if I were to do this again. I advise against using my strategy's execution logic in your own program.
