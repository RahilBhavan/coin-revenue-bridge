-- Parameters: :revenue_family, :volume_family, :information_cutoff, :target_period.
-- Pair only observations from one compatible definition family that were public
-- by the run's information cutoff. Target-period data is excluded defensively.
SELECT DISTINCT
    r.period_end,
    r.value_decimal AS revenue,
    v.value_decimal AS volume,
    r.scale AS revenue_scale,
    v.scale AS volume_scale
FROM reported_metric_observation AS r
JOIN reported_metric_observation AS v
  ON v.period_end = r.period_end
 AND v.currency = r.currency
WHERE r.metric_name = 'consumer_transaction_revenue'
  AND v.metric_name = 'consumer_trading_volume'
  AND r.definition_family = :revenue_family
  AND v.definition_family = :volume_family
  AND r.published_at <= :information_cutoff
  AND v.published_at <= :information_cutoff
  AND r.period_end < :target_period
ORDER BY r.period_end;
