# Local run

## Docker

```bash
docker compose build
docker compose run --rm platform
docker compose run --rm platform python scripts/show_results.py
docker compose run --rm platform pytest -q
```

The first command downloads/builds the local environment. The pipeline itself uses only local CPU, disk, Spark, and generated data.

## Without Docker

Requirements:

- Python 3.11
- Java 17

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python scripts/run_all.py
python scripts/show_results.py
pytest -q
```

On Windows PowerShell activate with:

```powershell
.\.venv\Scripts\Activate.ps1
```
