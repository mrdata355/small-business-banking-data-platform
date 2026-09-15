with source as (
    select * from {{ source('silver_lending', 'loan_application') }}
),
renamed as (
    select
        cast(application_id as {{ dbt.type_string() }}) as application_id,
        cast(customer_id as {{ dbt.type_string() }}) as customer_id,
        cast(business_id as {{ dbt.type_string() }}) as business_id,
        upper(trim(product_code)) as product_code,
        cast(requested_amount as numeric(18,2)) as requested_amount,
        upper(trim(use_of_funds)) as use_of_funds,
        upper(trim(application_status)) as application_status,
        cast(documents_complete as boolean) as documents_complete,
        cast(financial_package_complete as boolean) as financial_package_complete,
        cast(event_version as bigint) as event_version,
        cast(event_ts as timestamp) as event_ts,
        cast(source_system as {{ dbt.type_string() }}) as source_system,
        cast(trace_id as {{ dbt.type_string() }}) as trace_id,
        cast(updated_at as timestamp) as updated_at,
        {{ freshness_seconds('event_ts', 'updated_at') }} as processing_latency_seconds
    from source
)
select * from renamed
