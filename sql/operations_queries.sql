-- NYC 311 operations analysis examples
-- Assumes the cleaned table is named nyc311_q1_2025_clean.

-- 1) Monthly intake and closure rate
SELECT
  DATE_TRUNC('month', created_date) AS created_month,
  COUNT(*) AS requests,
  COUNT(*) FILTER (WHERE closed_flag) AS closed,
  AVG(closed_flag::int) AS closure_rate
FROM nyc311_q1_2025_clean
GROUP BY 1
ORDER BY 1;

-- 2) Resolution-risk comparison by agency
SELECT
  agency,
  COUNT(*) FILTER (WHERE closed_flag) AS closed_requests,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY resolution_hours)
    FILTER (WHERE closed_flag) AS median_resolution_hours,
  AVG((sla_breach_72h)::int) FILTER (WHERE closed_flag) AS breach_rate
FROM nyc311_q1_2025_clean
GROUP BY agency
HAVING COUNT(*) FILTER (WHERE closed_flag) >= 100
ORDER BY breach_rate DESC;

-- 3) Complaint-type priority queue
SELECT
  complaint_type,
  COUNT(*) FILTER (WHERE closed_flag) AS requests,
  AVG((sla_breach_72h)::int) FILTER (WHERE closed_flag) AS breach_rate,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY resolution_hours)
    FILTER (WHERE closed_flag) AS median_resolution_hours,
  COUNT(*) FILTER (WHERE closed_flag)
    * AVG((sla_breach_72h)::int) FILTER (WHERE closed_flag)
    * PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY resolution_hours)
        FILTER (WHERE closed_flag) AS priority_score
FROM nyc311_q1_2025_clean
GROUP BY complaint_type
HAVING COUNT(*) FILTER (WHERE closed_flag) >= 250
ORDER BY priority_score DESC;

-- 4) Intake-channel and weekend monitoring
SELECT
  open_data_channel_type,
  is_weekend,
  COUNT(*) AS requests,
  AVG((sla_breach_72h)::int) FILTER (WHERE closed_flag) AS breach_rate
FROM nyc311_q1_2025_clean
GROUP BY open_data_channel_type, is_weekend
ORDER BY breach_rate DESC;
