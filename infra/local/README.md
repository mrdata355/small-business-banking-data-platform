# Local production-equivalent stack

The full local stack uses Redpanda (Kafka API), Redpanda Console, MinIO (S3 API), Spark Structured Streaming, Delta Lake, MLflow, Prometheus and Grafana.

Run from the repository root:

```bash
docker compose -f docker-compose.full.yml up --build
```

Services:

- Redpanda Kafka API: `localhost:19092`
- Redpanda Console: `http://localhost:8080`
- Redpanda Schema Registry: `http://localhost:18081`
- MinIO S3 API: `http://localhost:9000`
- MinIO Console: `http://localhost:9001`
- Stream Gateway API: `http://localhost:8000`
- Spark UI: `http://localhost:4040`
- MLflow: `http://localhost:5000`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000`

Default local credentials are development-only and are configurable through environment variables.
