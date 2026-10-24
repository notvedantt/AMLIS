# Contracts

Typed models in `libs/contracts/models.py` are the only way services talk to each other. No raw dicts between planes.
Changing a field = breaking change: bump `CONTRACT_VERSION`, update every consumer in the same PR, and get both Vedant and Aditya to approve.
