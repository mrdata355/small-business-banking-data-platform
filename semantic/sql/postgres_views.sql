CREATE OR REPLACE VIEW sem_application_funnel AS
SELECT application_status,
       product_code,
       count(*) AS applications,
       sum(requested_amount)::numeric(18,2) AS requested_amount,
       count(*) FILTER (WHERE ready_for_underwriting) AS ready_for_underwriting
FROM canonical_applications
GROUP BY application_status, product_code;

CREATE OR REPLACE VIEW sem_treasury_activity AS
SELECT date_trunc('day', event_ts)::date AS activity_date,
       direction,
       transaction_status,
       count(*) AS transaction_count,
       sum(amount)::numeric(18,2) AS total_amount,
       avg(anomaly_score)::numeric(8,4) AS avg_anomaly_score,
       count(*) FILTER (WHERE risk_flag) AS risk_flag_count
FROM live_treasury_transaction
GROUP BY 1,2,3;

CREATE OR REPLACE VIEW sem_pipeline_quality AS
SELECT (SELECT count(*) FROM landing_objects) AS landing_objects,
       (SELECT count(*) FROM stream_arrivals) AS stream_arrivals,
       (SELECT count(*) FROM clean_events) AS clean_events,
       (SELECT count(*) FROM quarantine_events) AS quarantined_events,
       (SELECT count(*) FROM pipeline_audit WHERE outcome='DUPLICATE_IGNORED') AS duplicates_ignored,
       CASE WHEN (SELECT count(*) FROM stream_arrivals)=0 THEN 0
            ELSE round((SELECT count(*)::numeric FROM quarantine_events)/(SELECT count(*)::numeric FROM stream_arrivals),4)
       END AS quarantine_rate;

CREATE OR REPLACE VIEW sem_customer_sentiment AS
SELECT date_trunc('hour', created_at) AS hour,
       channel,
       sentiment_label,
       count(*) AS interactions,
       round(avg(sentiment_score),4) AS avg_sentiment
FROM customer_interactions
GROUP BY 1,2,3;

CREATE OR REPLACE VIEW sem_model_risk AS
SELECT model_name,
       model_version,
       predicted_risk_band,
       count(*) AS predictions,
       round(avg(risk_probability),4) AS avg_risk_probability,
       max(scored_at) AS last_scored_at
FROM live_model_prediction
GROUP BY 1,2,3;
