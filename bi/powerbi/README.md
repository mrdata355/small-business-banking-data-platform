# Power BI

The semantic PostgreSQL views are deployed in the live demo database and are the intended BI contract.

Open `oakbridge-live.pbids` with Power BI Desktop to preconfigure the server and database. Authentication is intentionally not stored in the repository. Power BI will prompt for PostgreSQL credentials.

Semantic views:

- `public.sem_application_funnel`
- `public.sem_treasury_activity`
- `public.sem_pipeline_quality`
- `public.sem_customer_sentiment`
- `public.sem_model_risk`

`PowerQuery.m` contains equivalent Power Query M definitions for the same views.

Recommended report pages:

1. Lending funnel and requested amount
2. Underwriting readiness
3. Treasury volume and returned-payment rate
4. Pipeline quality and quarantine
5. Customer sentiment
6. Model risk distribution

The repository never stores database passwords or tokens.
