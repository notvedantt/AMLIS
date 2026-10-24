    # data_plane

    External I/O, point-in-time store, data-integrity gate (staleness, range, cross-source).

    | | |
    |---|---|
    | Tier | 0 (Foundations) |
    | Owner | Aditya |
    | Second reviewer | Vedant |

    ## Rules
    - Import only from `libs.*`. Never import another service's internals; talk through `libs.contracts` types.
    - Keep one public entry point in `__init__.py`.

    ## Tasks
    - T0.5 (Aditya): Point-in-time market data adapter and store (knowable_at stamps)
- T0.6 (Vedant): Data-integrity gate (staleness, range sanity, cross-source agreement)
- T0.7 (Rushikesh): Macro calendar loader (CPI, NFP, rate decisions)
