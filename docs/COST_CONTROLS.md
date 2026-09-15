# Cost controls

The repository defaults to local services so the full logical platform can be demonstrated without continuously running paid cloud infrastructure.

Cloud controls to apply before enabling production resources:

- AWS Budgets and billing alarms
- Kinesis on-demand or explicitly bounded shard count based on measured throughput
- S3 lifecycle policies for raw/history tiers
- Databricks/serverless autoscaling limits and workload policies
- automatic termination for interactive compute
- job-specific compute instead of permanently running development clusters
- partition/file compaction to reduce object-store and metadata overhead
- CloudWatch alert thresholds on retries, throttling and error rate
- MLflow artifact lifecycle policy
- environment tags and per-domain cost allocation

`terraform plan` is safe for review. `terraform apply` is intentionally not automated by this repository.
