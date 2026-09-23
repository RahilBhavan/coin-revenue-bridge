"""Small, auditable forecasting and variance-analysis core."""

from __future__ import annotations

import csv
import sqlite3
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable, Sequence, Tuple

REVENUE = "consumer_transaction_revenue"
VOLUME = "consumer_trading_volume"
REQUIRED_COLUMNS = {
    "observation_id",
    "metric_name",
    "period_start",
    "period_end",
    "value_decimal",
    "currency",
    "scale",
    "definition_id",
    "definition_family",
    "original_or_recast",
    "source_id",
    "published_at",
    "evidence_class",
    "reviewer_status",
}
PROCESSED_COLUMNS = {
    "observation_id", "period", "period_end", "metric_name", "value_decimal",
    "unit", "definition_family", "original_or_recast", "source_id",
    "published_at_utc", "evidence_locator", "evidence_note", "reviewer_status",
}
ANALYTICS_READY_COLUMNS = {
    "observation_id", "period", "period_end", "metric_name", "value_decimal",
    "currency", "scale", "definition_family", "metric_definition_family",
    "vintage_status", "source_id", "published_at", "analysis_use",
}


class AnalysisError(ValueError):
    """Raised when analytical inputs fail closed."""


@dataclass(frozen=True)
class Forecast:
    target_period: str
    information_cutoff: str
    definition_family: str
    prior_quarter: Decimal
    prior_year: Decimal | None
    driver_revenue: Decimal
    forecast_volume: Decimal
    forecast_yield: Decimal
    input_periods: Tuple[str, ...]


@dataclass(frozen=True)
class Score:
    mae: Decimal
    signed_bias: Decimal
    wape: Decimal
    count: int


@dataclass(frozen=True)
class Bridge:
    forecast_revenue: Decimal
    actual_revenue: Decimal
    forecast_volume: Decimal
    actual_volume: Decimal
    forecast_yield: Decimal
    actual_yield: Decimal
    volume_effect: Decimal
    yield_effect: Decimal
    residual: Decimal
    bridge_order: str = "fixed-volume-then-yield"


@dataclass(frozen=True)
class DescriptiveBridge:
    analysis_type: str
    comparison_period: str
    target_period: str
    information_cutoff: str
    definition_family: str
    revenue_unit: str
    volume_unit: str
    effective_yield_unit: str
    comparison_revenue: Decimal
    target_revenue: Decimal
    revenue_change: Decimal
    comparison_volume: Decimal
    target_volume: Decimal
    comparison_yield: Decimal
    target_yield: Decimal
    volume_effect: Decimal
    yield_effect: Decimal
    residual: Decimal
    bridge_order: str = "fixed-volume-then-yield"


@dataclass(frozen=True)
class SymmetricAttribution:
    revenue_change: Decimal
    volume_first_volume: Decimal
    volume_first_yield: Decimal
    yield_first_volume: Decimal
    yield_first_yield: Decimal
    symmetric_volume: Decimal
    symmetric_yield: Decimal
    residual: Decimal


@dataclass(frozen=True)
class PlanningSensitivity:
    volume: Decimal
    effective_yield: Decimal
    implied_revenue: Decimal
    revenue_change: Decimal


def _iso_date(value: str, field: str) -> str:
    try:
        date.fromisoformat(value)
    except ValueError as error:
        raise AnalysisError(f"invalid {field}: {value!r}") from error
    return value


def _decimal(value: str, field: str) -> Decimal:
    try:
        result = Decimal(value)
    except InvalidOperation as error:
        raise AnalysisError(f"invalid decimal {field}: {value!r}") from error
    if not result.is_finite():
        raise AnalysisError(f"non-finite decimal {field}: {value!r}")
    return result


def ingest_csv(connection: sqlite3.Connection, path: Path) -> int:
    """Validate and insert the planned long-form reported-metrics CSV."""
    with Path(path).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or ())
        is_processed = PROCESSED_COLUMNS.issubset(fields)
        is_analytics_ready = ANALYTICS_READY_COLUMNS.issubset(fields)
        missing = REQUIRED_COLUMNS.difference(fields)
        if missing and not is_processed and not is_analytics_ready:
            raise AnalysisError(f"missing CSV columns: {', '.join(sorted(missing))}")
        rows = []
        for line_number, row in enumerate(reader, start=2):
            if is_processed or is_analytics_ready:
                try:
                    if is_processed:
                        currency, scale = row["unit"].split("_", 1)
                    else:
                        currency, scale = row["currency"], row["scale"]
                    year, quarter = row["period"].split("-Q")
                    start_month = 1 + (int(quarter) - 1) * 3
                    period_start = f"{int(year):04d}-{start_month:02d}-01"
                except (ValueError, AttributeError) as error:
                    raise AnalysisError(f"invalid processed row at line {line_number}") from error
                row = {
                    **row,
                    "period_start": period_start,
                    "currency": currency,
                    "scale": scale,
                    "definition_id": row.get("metric_definition_family", row["definition_family"]),
                    "original_or_recast": row.get("vintage_status", row.get("original_or_recast")),
                    "published_at": row.get("published_at", row.get("published_at_utc"))[:10],
                    "evidence_class": row.get("evidence_locator", "normalized_source_row"),
                    "reviewer_status": row.get("reviewer_status", "normalized_from_reviewed_source"),
                    "analysis_use": row.get("analysis_use", "descriptive_only"),
                }
            if row["metric_name"] not in {REVENUE, VOLUME}:
                raise AnalysisError(f"unsupported metric at line {line_number}")
            _iso_date(row["period_end"], "period_end")
            _iso_date(row["period_start"], "period_start")
            _iso_date(row["published_at"], "published_at")
            _decimal(row["value_decimal"], "value_decimal")
            if not all(row[column].strip() for column in REQUIRED_COLUMNS):
                raise AnalysisError(f"blank required value at line {line_number}")
            columns = (
                "observation_id", "metric_name", "period_start", "period_end",
                "value_decimal", "currency", "scale", "definition_id",
                "definition_family", "original_or_recast", "source_id", "published_at",
                "evidence_class", "reviewer_status",
            )
            rows.append(tuple(row[column] for column in columns) + (
                row.get("analysis_use", "synthetic_test"),
            ))
    try:
        with connection:
            connection.executemany(
                "INSERT INTO reported_metric_observation VALUES "
                "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                rows,
            )
    except sqlite3.IntegrityError as error:
        raise AnalysisError(f"duplicate or invalid observation: {error}") from error
    return len(rows)


def _median(values: Sequence[Decimal]) -> Decimal:
    if not values:
        raise AnalysisError("median requires at least one value")
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[midpoint]
    return (ordered[midpoint - 1] + ordered[midpoint]) / Decimal(2)


def _to_millions(value: Decimal, scale: str) -> Decimal:
    factors = {"millions": Decimal(1), "billions": Decimal(1000)}
    try:
        return value * factors[scale.lower()]
    except KeyError as error:
        raise AnalysisError(f"unsupported scale: {scale!r}") from error


def _component_families(definition_family: str) -> Tuple[str, str]:
    if "|" not in definition_family:
        return definition_family, definition_family
    revenue_family, volume_family = definition_family.split("|", 1)
    if not revenue_family or not volume_family:
        raise AnalysisError("component definition families must be nonblank")
    return revenue_family, volume_family


def _prior_year(period: str) -> str:
    parsed = date.fromisoformat(period)
    try:
        return parsed.replace(year=parsed.year - 1).isoformat()
    except ValueError:
        return parsed.replace(year=parsed.year - 1, day=28).isoformat()


def _prior_quarter(period: str) -> str:
    parsed = date.fromisoformat(period)
    quarter_ends = {
        (3, 31): (parsed.year - 1, 12, 31),
        (6, 30): (parsed.year, 3, 31),
        (9, 30): (parsed.year, 6, 30),
        (12, 31): (parsed.year, 9, 30),
    }
    previous = quarter_ends.get((parsed.month, parsed.day))
    if previous is None:
        raise AnalysisError("target_period must be a calendar-quarter end")
    return date(*previous).isoformat()


def forecast_target(
    connection: sqlite3.Connection,
    target_period: str,
    information_cutoff: str,
    definition_family: str,
    growth_floor: Decimal = Decimal("-0.50"),
    growth_ceiling: Decimal = Decimal("0.50"),
) -> Forecast:
    """Forecast one quarter from only compatible observations public by cutoff."""
    _iso_date(target_period, "target_period")
    _iso_date(information_cutoff, "information_cutoff")
    if growth_floor > growth_ceiling:
        raise AnalysisError("growth floor exceeds ceiling")
    revenue_family, volume_family = _component_families(definition_family)
    analysis_uses = {
        row[0] for row in connection.execute(
            "SELECT DISTINCT analysis_use FROM reported_metric_observation "
            "WHERE (definition_family = ? OR definition_family = ?)",
            (revenue_family, volume_family),
        )
    }
    if "descriptive_only" in analysis_uses:
        raise AnalysisError("forecast mode refused: selected observations are descriptive_only")
    metric_period_rows = connection.execute(
        "SELECT metric_name, period_end, value_decimal, currency, scale "
        "FROM reported_metric_observation "
        "WHERE ((definition_family = ? AND metric_name = ?) "
        "OR (definition_family = ? AND metric_name = ?)) "
        "AND published_at <= ? AND period_end < ?",
        (revenue_family, REVENUE, volume_family, VOLUME, information_cutoff, target_period),
    ).fetchall()
    revenue_periods = {row[1] for row in metric_period_rows if row[0] == REVENUE}
    volume_periods = {row[1] for row in metric_period_rows if row[0] == VOLUME}
    if revenue_periods != volume_periods:
        raise AnalysisError("missing revenue or volume for a compatible historical period")
    if "forecast_eligible" in analysis_uses and len(revenue_periods) < 12:
        raise AnalysisError("forecast mode requires at least 12 comparable historical quarters")
    variants = {}
    currencies_by_period = {}
    for metric, period, value, currency, scale in metric_period_rows:
        variants.setdefault((metric, period), set()).add((value, currency, scale))
        currencies_by_period.setdefault(period, set()).add(currency)
    if any(len(values) != 1 for values in variants.values()):
        raise AnalysisError("conflicting overlapping observations require reconciliation")
    if any(len(currencies) != 1 for currencies in currencies_by_period.values()):
        raise AnalysisError("revenue and volume currencies are incompatible")
    sql_path = Path(__file__).resolve().parents[2] / "sql" / "cutoff_inputs.sql"
    rows = connection.execute(
        sql_path.read_text(encoding="utf-8"),
        {
            "revenue_family": revenue_family,
            "volume_family": volume_family,
            "information_cutoff": information_cutoff,
            "target_period": target_period,
        },
    ).fetchall()
    if not rows:
        other_history = connection.execute(
            "SELECT 1 FROM reported_metric_observation WHERE period_end < ? LIMIT 1",
            (target_period,),
        ).fetchone()
        if other_history:
            raise AnalysisError("incompatible definition family or no compatible history")
        raise AnalysisError("no compatible history available by information cutoff")

    periods = [row[0] for row in rows]
    revenues = [_to_millions(_decimal(row[1], "revenue"), row[3]) for row in rows]
    volumes = [_to_millions(_decimal(row[2], "volume"), row[4]) for row in rows]
    if any(volume <= 0 for volume in volumes):
        raise AnalysisError("all historical periods require positive volume")

    revenue_by_period = dict(zip(periods, revenues))
    prior_quarter_period = _prior_quarter(target_period)
    if prior_quarter_period not in revenue_by_period:
        raise AnalysisError("prior-quarter baseline is unavailable")
    prior_quarter = revenue_by_period[prior_quarter_period]
    prior_year = revenue_by_period.get(_prior_year(target_period))

    recent_volumes = volumes[-4:]
    growths = [
        (current / previous) - Decimal(1)
        for previous, current in zip(recent_volumes, recent_volumes[1:])
    ]
    median_growth = _median(growths) if growths else Decimal(0)
    clipped_growth = min(growth_ceiling, max(growth_floor, median_growth))
    forecast_volume = volumes[-1] * (Decimal(1) + clipped_growth)
    if forecast_volume <= 0:
        raise AnalysisError("forecast requires positive volume")

    yields = [revenue / volume for revenue, volume in zip(revenues[-4:], volumes[-4:])]
    forecast_yield = _median(yields)
    driver_revenue = forecast_volume * forecast_yield
    return Forecast(
        target_period=target_period,
        information_cutoff=information_cutoff,
        definition_family=definition_family,
        prior_quarter=prior_quarter,
        prior_year=prior_year,
        driver_revenue=driver_revenue,
        forecast_volume=forecast_volume,
        forecast_yield=forecast_yield,
        input_periods=tuple(periods),
    )


def score_forecasts(rows: Iterable[Tuple[Decimal, Decimal]]) -> Score:
    """Return MAE, signed forecast bias (forecast - actual), and WAPE."""
    pairs = list(rows)
    if not pairs:
        raise AnalysisError("at least one holdout is required")
    errors = [forecast - actual for forecast, actual in pairs]
    actual_total = sum((abs(actual) for _, actual in pairs), Decimal(0))
    if actual_total == 0:
        raise AnalysisError("actual total must be nonzero for WAPE")
    count = Decimal(len(pairs))
    return Score(
        mae=sum((abs(error) for error in errors), Decimal(0)) / count,
        signed_bias=sum(errors, Decimal(0)) / count,
        wape=sum((abs(error) for error in errors), Decimal(0)) / actual_total,
        count=len(pairs),
    )


def compute_bridge(
    forecast_volume: Decimal,
    actual_volume: Decimal,
    forecast_yield: Decimal,
    actual_revenue: Decimal,
) -> Bridge:
    """Compute an exact, fixed-order volume-then-yield variance bridge."""
    if forecast_volume <= 0 or actual_volume <= 0:
        raise AnalysisError("bridge requires positive volume")
    forecast_revenue = forecast_volume * forecast_yield
    actual_yield = actual_revenue / actual_volume
    volume_effect = (actual_volume - forecast_volume) * forecast_yield
    yield_effect = actual_volume * (actual_yield - forecast_yield)
    residual = actual_revenue - forecast_revenue - volume_effect - yield_effect
    return Bridge(
        forecast_revenue=forecast_revenue,
        actual_revenue=actual_revenue,
        forecast_volume=forecast_volume,
        actual_volume=actual_volume,
        forecast_yield=forecast_yield,
        actual_yield=actual_yield,
        volume_effect=volume_effect,
        yield_effect=yield_effect,
        residual=residual,
    )


def symmetric_attribution(
    starting_revenue: Decimal,
    ending_revenue: Decimal,
    starting_volume: Decimal,
    ending_volume: Decimal,
) -> SymmetricAttribution:
    """Average both exact two-factor bridge orders to split the interaction term."""
    if starting_volume <= 0 or ending_volume <= 0:
        raise AnalysisError("symmetric attribution requires positive volume")
    starting_yield = starting_revenue / starting_volume
    ending_yield = ending_revenue / ending_volume
    volume_first_volume = (ending_volume - starting_volume) * starting_yield
    volume_first_yield = ending_volume * (ending_yield - starting_yield)
    yield_first_yield = starting_volume * (ending_yield - starting_yield)
    yield_first_volume = (ending_volume - starting_volume) * ending_yield
    symmetric_volume = (volume_first_volume + yield_first_volume) / Decimal(2)
    symmetric_yield = (volume_first_yield + yield_first_yield) / Decimal(2)
    revenue_change = ending_revenue - starting_revenue
    residual = revenue_change - symmetric_volume - symmetric_yield
    return SymmetricAttribution(
        revenue_change=revenue_change,
        volume_first_volume=volume_first_volume,
        volume_first_yield=volume_first_yield,
        yield_first_volume=yield_first_volume,
        yield_first_yield=yield_first_yield,
        symmetric_volume=symmetric_volume,
        symmetric_yield=symmetric_yield,
        residual=residual,
    )


def planning_sensitivity(
    reference_revenue: Decimal,
    reference_volume: Decimal,
    volume_change: Decimal,
    yield_change: Decimal,
) -> PlanningSensitivity:
    """Apply explicit volume and yield changes around an actual reference case."""
    if reference_volume <= 0:
        raise AnalysisError("planning sensitivity requires positive reference volume")
    volume = reference_volume * (Decimal(1) + volume_change)
    effective_yield = reference_revenue / reference_volume + yield_change
    if volume <= 0 or effective_yield < 0:
        raise AnalysisError("planning sensitivity produces an invalid volume or yield")
    implied_revenue = volume * effective_yield
    return PlanningSensitivity(
        volume=volume,
        effective_yield=effective_yield,
        implied_revenue=implied_revenue,
        revenue_change=implied_revenue - reference_revenue,
    )


def actual_pair(
    connection: sqlite3.Connection,
    target_period: str,
    definition_family: str,
    information_cutoff: str | None = None,
) -> Tuple[Decimal, Decimal]:
    revenue_family, volume_family = _component_families(definition_family)
    cutoff_clause = " AND published_at <= ?" if information_cutoff else ""
    parameters = [target_period, revenue_family, REVENUE, volume_family, VOLUME]
    if information_cutoff:
        _iso_date(information_cutoff, "information_cutoff")
        parameters.append(information_cutoff)
    rows = connection.execute(
        "SELECT metric_name, value_decimal, scale FROM reported_metric_observation "
        "WHERE period_end = ? AND ((definition_family = ? AND metric_name = ?) "
        "OR (definition_family = ? AND metric_name = ?))" + cutoff_clause,
        parameters,
    ).fetchall()
    if len(rows) != 2:
        raise AnalysisError("target actuals are missing or ambiguous")
    values = {
        metric: _to_millions(_decimal(value, metric), scale)
        for metric, value, scale in rows
    }
    if set(values) != {REVENUE, VOLUME}:
        raise AnalysisError("target actual revenue and volume are required for bridge")
    return values[REVENUE], values[VOLUME]


def descriptive_bridge(
    connection: sqlite3.Connection,
    comparison_period: str,
    target_period: str,
    information_cutoff: str,
    definition_family: str,
) -> DescriptiveBridge:
    """Explain a reported revenue change; this is not a forecast or causal model."""
    if comparison_period >= target_period:
        raise AnalysisError("comparison_period must precede target_period")
    comparison_revenue, comparison_volume = actual_pair(
        connection, comparison_period, definition_family, information_cutoff
    )
    target_revenue, target_volume = actual_pair(
        connection, target_period, definition_family, information_cutoff
    )
    bridge = compute_bridge(
        comparison_volume,
        target_volume,
        comparison_revenue / comparison_volume,
        target_revenue,
    )
    return DescriptiveBridge(
        analysis_type="descriptive",
        comparison_period=comparison_period,
        target_period=target_period,
        information_cutoff=information_cutoff,
        definition_family=definition_family,
        revenue_unit="USD_millions",
        volume_unit="USD_millions",
        effective_yield_unit="USD_per_USD",
        comparison_revenue=comparison_revenue,
        target_revenue=target_revenue,
        revenue_change=target_revenue - comparison_revenue,
        comparison_volume=comparison_volume,
        target_volume=target_volume,
        comparison_yield=bridge.forecast_yield,
        target_yield=bridge.actual_yield,
        volume_effect=bridge.volume_effect,
        yield_effect=bridge.yield_effect,
        residual=bridge.residual,
    )
