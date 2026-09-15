let
    Server = "ep-summer-recipe-argodi6k-pooler.c-4.us-west-2.aws.neon.tech",
    Database = "banking_demo",
    Source = PostgreSQL.Database(Server, Database, [CreateNavigationProperties=false]),
    ApplicationFunnel = Source{[Schema="public", Item="sem_application_funnel"]}[Data],
    TreasuryActivity = Source{[Schema="public", Item="sem_treasury_activity"]}[Data],
    PipelineQuality = Source{[Schema="public", Item="sem_pipeline_quality"]}[Data],
    CustomerSentiment = Source{[Schema="public", Item="sem_customer_sentiment"]}[Data],
    ModelRisk = Source{[Schema="public", Item="sem_model_risk"]}[Data]
in
    [
        ApplicationFunnel=ApplicationFunnel,
        TreasuryActivity=TreasuryActivity,
        PipelineQuality=PipelineQuality,
        CustomerSentiment=CustomerSentiment,
        ModelRisk=ModelRisk
    ]
