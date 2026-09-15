FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends openjdk-17-jre-headless bash \
    && rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PYSPARK_PYTHON=python
ENV PYTHONUNBUFFERED=1

WORKDIR /workspace
COPY pyproject.toml README.md ./
COPY src ./src
COPY tests ./tests
COPY scripts ./scripts
COPY sample_data ./sample_data
COPY docs ./docs
COPY sql ./sql
COPY orchestration ./orchestration
COPY notebooks ./notebooks
COPY databricks.yml ./
COPY resources ./resources

RUN pip install --no-cache-dir -e ".[dev]"

CMD ["python", "scripts/run_all.py"]
