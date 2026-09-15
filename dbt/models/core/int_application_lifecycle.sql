{{ config(
    materialized='incremental',
    unique_key='application_id',
    incremental_strategy='merge'
) }}

with applications as (
    select * from {{ ref('stg_loan_application') }}
    {% if is_incremental() %}
    where updated_at >= (select coalesce(max(updated_at), cast('1900-01-01' as timestamp)) from {{ this }})
    {% endif %}
),
identity as (
    select
        application_id,
        upper(trim(verification_status)) as identity_verification_status,
        verification_ts
    from {{ source('silver_risk', 'identity_verification') }}
),
conformed as (
    select
        a.*,
        coalesce(i.identity_verification_status, 'PENDING') as identity_verification_status,
        i.verification_ts,
        (
            a.documents_complete
            and a.financial_package_complete
            and coalesce(i.identity_verification_status, 'PENDING') = 'VERIFIED'
        ) as ready_for_underwriting,
        case
            when a.application_status = 'FUNDED' then 'FUNDED'
            when a.application_status = 'DECISIONED' then 'DECISIONED'
            when a.documents_complete and a.financial_package_complete and coalesce(i.identity_verification_status, 'PENDING') = 'VERIFIED' then 'READY'
            when not a.documents_complete then 'DOCUMENTS'
            when not a.financial_package_complete then 'FINANCIAL_PACKAGE'
            when coalesce(i.identity_verification_status, 'PENDING') <> 'VERIFIED' then 'IDENTITY'
            else 'REVIEW'
        end as operational_stage
    from applications a
    left join identity i using (application_id)
)
select * from conformed
