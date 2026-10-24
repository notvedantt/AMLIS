    # llm_research

    LangGraph agents: analysts, debate, trader/risk advisory tiers, memory and reflection.

    | | |
    |---|---|
    | Tier | 2 (Multi-LLM research layer) |
    | Owner | Aditya |
    | Second reviewer | Vedant |

    ## Rules
    - Import only from `libs.*`. Never import another service's internals; talk through `libs.contracts` types.
    - Keep one public entry point in `__init__.py`.

    ## Tasks
    - T2.1 (Aditya): LangGraph skeleton, multi-provider LLM abstraction, per-call cost tracking
- T2.2 (Aditya): Analysts: technical and fundamental
- T2.3 (Vedant): Analysts: news, economic calendar, event/shock, cross-asset
- T2.4 (Rushikesh): Analysts: sentiment and company news (using the prompt template)
- T2.5 (Vedant): Debate tier: bull, bear, base-case researchers and facilitator
- T2.6 (Aditya): Layered memory (short/mid/long) and reflection step
- T2.8 (Rushikesh): Prompt library and LLM call logging
