    # system1

    Fine-tuned encoder decision model: dataset builder, heads, local serving.

    | | |
    |---|---|
    | Tier | 7 (System 1 fine-tuning) |
    | Owner | Vedant |
    | Second reviewer | Aditya |

    ## Rules
    - Import only from `libs.*`. Never import another service's internals; talk through `libs.contracts` types.
    - Keep one public entry point in `__init__.py`.

    ## Tasks
    - T7.1 (Aditya): Dataset builder from ledger logs (point-in-time labels, per-task splits)
- T7.2 (Vedant): Fine-tuning pipeline for the decision model (full fine-tune on GPU)
- T7.3 (Vedant): Task heads: router escalation and event severity
- T7.4 (Aditya): Task heads: verifier grounding and compliance check
- T7.5 (Vedant): Local microservice serving and latency benchmark
