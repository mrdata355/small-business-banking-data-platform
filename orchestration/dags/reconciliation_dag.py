from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator

with DAG(
    dag_id="banking_pipeline_reconciliation",
    start_date=datetime(2026, 1, 1),
    schedule="0 * * * *",
    catchup=False,
    tags=["data-platform", "reconciliation"],
) as dag:
    reconcile = BashOperator(
        task_id="reconcile_application_pipeline",
        bash_command="python -m oakbridge.jobs.reconciliation",
    )
