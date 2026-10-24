    # evaluation

    Rolling-window, cost-aware backtesting, metrics, baselines, hypothesis tests.

    | | |
    |---|---|
    | Tier | 0 (Foundations) |
    | Owner | Vedant |
    | Second reviewer | Aditya |

    ## Rules
    - Import only from `libs.*`. Never import another service's internals; talk through `libs.contracts` types.
    - Keep one public entry point in `__init__.py`.

    ## Tasks
    - T0.10 (Vedant): Evaluation harness: rolling backtest, cost model, Sharpe/Sortino/drawdown
- T1.1 (Rushikesh): Baselines: buy-and-hold and simple momentum inside the harness
- T2.9 (Vedant): Baseline arms: single-LLM, majority-vote, TradingAgents-style
- T4.4 (Aditya): Static-router baseline and H7 evaluation
