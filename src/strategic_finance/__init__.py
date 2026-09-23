"""Cutoff-safe strategic finance analytics."""

from .core import (
    AnalysisError,
    Bridge,
    DescriptiveBridge,
    Forecast,
    Score,
    compute_bridge,
    descriptive_bridge,
    forecast_target,
    ingest_csv,
    score_forecasts,
)

__all__ = [
    "AnalysisError",
    "Bridge",
    "DescriptiveBridge",
    "Forecast",
    "Score",
    "compute_bridge",
    "descriptive_bridge",
    "forecast_target",
    "ingest_csv",
    "score_forecasts",
]
