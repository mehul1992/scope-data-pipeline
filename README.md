# Scope Data Pipeline

Scaffolded project structure for a FastAPI, PostgreSQL, and Airflow based data pipeline.

## Prerequisites

- Git
- Docker and Docker Compose v2

## Quick start

1. Clone the repository:

```bash
git clone <project_url>
cd scope-data-pipeline
```

Replace `<project_url>` with your Git remote URL.

2. Start the stack in the background:

```bash
docker compose up -d
```

Services include PostgreSQL, the API (port **8000**), and Airflow (port **8080**).

## API documentation

Interactive OpenAPI docs for the FastAPI service: [http://localhost:8000/docs](http://localhost:8000/docs)

## Running tests

Install dev dependencies and run pytest from the project root:

```bash
pip install -e ".[dev]"
pytest tests/ -q
```

## Airflow credentials

To read the generated Simple Auth Manager passwords file inside the Airflow container:

1. Open a shell in the Airflow container:

```bash
docker exec -it scope_airflow bash
```

2. Show the generated passwords file:

```bash
cat simple_auth_manager_passwords.json.generated
```

Use the credentials from that JSON to sign in to the Airflow UI at [http://localhost:8080](http://localhost:8080).

If the file path differs in your Airflow image, search from the Airflow home directory (typically `/opt/airflow`):

```bash
find /opt/airflow -name 'simple_auth_manager_passwords.json.generated' 2>/dev/null
```
