{% macro safe_divide(numerator, denominator, default_value=0) -%}
case
  when {{ denominator }} is null or {{ denominator }} = 0 then {{ default_value }}
  else ({{ numerator }} * 1.0) / {{ denominator }}
end
{%- endmacro %}

{% macro freshness_seconds(event_ts, processing_ts='current_timestamp') -%}
extract(epoch from ({{ processing_ts }} - {{ event_ts }}))
{%- endmacro %}

{% macro boolean_rate(expression) -%}
avg(case when {{ expression }} then 1.0 else 0.0 end)
{%- endmacro %}

{% macro risk_adjusted_priority(business_value, risk_reduction, urgency, effort) -%}
(
  coalesce({{ business_value }}, 0)
  + coalesce({{ risk_reduction }}, 0)
  + coalesce({{ urgency }}, 0)
) / greatest(coalesce({{ effort }}, 1), 0.25)
{%- endmacro %}

{% macro dbt_surrogate_key(fields) -%}
md5(
  concat_ws(
    '||'
    {% for field in fields %}
      , coalesce(cast({{ field }} as {{ dbt.type_string() }}), '__null__')
    {% endfor %}
  )
)
{%- endmacro %}
