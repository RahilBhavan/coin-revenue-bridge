-- Q3-to-Q4 2024 descriptive consumer transaction revenue bridge.
-- This query is an algebraic decomposition, not a forecast or causal model.
-- It expects reported_metric_observation populated from the reviewed CSV.

WITH selected AS (
    SELECT
        period_end,
        metric_name,
        CAST(value_decimal AS REAL) *
            CASE scale WHEN 'billions' THEN 1000.0 ELSE 1.0 END AS value_usd_mm
    FROM reported_metric_observation
    WHERE definition_family = 'PAIR-REV-POST2024Q1-VOL-SPOT-PRE2025Q4'
      AND analysis_use = 'descriptive_only'
      AND period_end IN ('2024-09-30', '2024-12-31')
      AND published_at <= '2025-02-13T23:59:59Z'
), quarter_values AS (
    SELECT
        period_end,
        MAX(CASE WHEN metric_name = 'consumer_transaction_revenue' THEN value_usd_mm END) AS revenue_mm,
        MAX(CASE WHEN metric_name = 'consumer_trading_volume' THEN value_usd_mm END) AS volume_mm
    FROM selected
    GROUP BY period_end
), paired AS (
    SELECT
        from_q.revenue_mm AS from_revenue_mm,
        to_q.revenue_mm AS to_revenue_mm,
        from_q.volume_mm AS from_volume_mm,
        to_q.volume_mm AS to_volume_mm,
        from_q.revenue_mm / from_q.volume_mm AS from_yield,
        to_q.revenue_mm / to_q.volume_mm AS to_yield
    FROM quarter_values AS from_q
    CROSS JOIN quarter_values AS to_q
    WHERE from_q.period_end = '2024-09-30'
      AND to_q.period_end = '2024-12-31'
)
SELECT
    to_revenue_mm - from_revenue_mm AS revenue_change_mm,
    (to_volume_mm - from_volume_mm) * from_yield AS volume_effect_mm,
    to_volume_mm * (to_yield - from_yield) AS effective_yield_effect_mm,
    (to_revenue_mm - from_revenue_mm)
      - ((to_volume_mm - from_volume_mm) * from_yield)
      - (to_volume_mm * (to_yield - from_yield)) AS residual_mm
FROM paired;
