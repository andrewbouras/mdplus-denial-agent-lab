"""Plinth trajectory-contract adapters for the policy-retrieval env.

This package holds the *repo-local* glue that maps our computed KISS oracle
(``synthetic_harness.kiss_oracle.compute_oracle``) onto the Plinth
``training_unit`` rating shape, and nothing else. It does NOT re-implement the
oracle and it does NOT touch any Plinth app file — it only translates an
already-computed oracle verdict into the operator-facing rating pre-fill.
"""

from .oracle_to_rating import (
    DERIVED_BY,
    map_oracle_to_rating,
    build_training_unit,
)

__all__ = ["DERIVED_BY", "map_oracle_to_rating", "build_training_unit"]
