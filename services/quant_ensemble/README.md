    # quant_ensemble

    Boosted trees, sequence models, stacking meta-learner, calibrated predictions.

    | | |
    |---|---|
    | Tier | 1 (Quant baseline) |
    | Owner | Aditya |
    | Second reviewer | Vedant |

    ## Rules
    - Import only from `libs.*`. Never import another service's internals; talk through `libs.contracts` types.
    - Keep one public entry point in `__init__.py`.

    ## Tasks
    - T1.2 (Aditya): Gradient-boosted tree model and training pipeline
- T1.3 (Vedant): Sequence model (LSTM/TCN) on GPU
- T1.4 (Aditya): Stacking meta-learner and calibrated probabilities
