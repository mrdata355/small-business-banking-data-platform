# Deployment targets

## Local full stack

`docker-compose.full.yml` is the complete zero-cloud provisioning path for Kafka-compatible streaming, S3-compatible object storage, Spark/Delta processing, MLflow, Prometheus and Grafana.

## Databricks

`databricks.yml` and `resources/jobs.yml` define deployable jobs. The notebook source under `notebooks/databricks/` is intentionally thin; packaged Python modules own processing logic.

Databricks account console:

https://accounts.cloud.databricks.com/

Workspace-specific notebook deep links require a workspace hostname and workspace object/repo id and are therefore not committed as a fabricated URL.

## AWS

`infra/terraform/` contains Kinesis, S3, DynamoDB, Glue, Lambda, ECS/Fargate, EMR Serverless, CloudWatch/SNS, ECR and IAM definitions. AWS deployment is opt-in because provisioned services can create charges.

## Web console

The public Vercel deployment provides persistent generated data, data-quality, canonical merge, observability, automation, sentiment and model-scoring evidence without continuously running paid streaming infrastructure.
