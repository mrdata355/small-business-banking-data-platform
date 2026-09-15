with source as (
    select * from {{ source('silver_treasury', 'ach_transaction') }}
),
normalized as (
    select
        cast(transaction_id as {{ dbt.type_string() }}) as transaction_id,
        cast(event_ts as timestamp) as event_ts,
        cast(account_id as {{ dbt.type_string() }}) as account_id,
        cast(business_id as {{ dbt.type_string() }}) as business_id,
        upper(trim(direction)) as direction,
        cast(amount as numeric(18,2)) as amount,
        upper(trim(sec_code)) as sec_code,
        upper(trim(transaction_status)) as transaction_status,
        cast(counterparty_token as {{ dbt.type_string() }}) as counterparty_token,
        cast(source_system as {{ dbt.type_string() }}) as source_system,
        case when upper(trim(direction)) = 'DEBIT' then -1 else 1 end * cast(amount as numeric(18,2)) as signed_amount,
        case when upper(trim(transaction_status)) = 'RETURNED' then true else false end as is_returned
    from source
)
select * from normalized
