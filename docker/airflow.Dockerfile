FROM apache/airflow:3.0.1-python3.11

USER root

# Application code for DAG imports (config, utils). Do not install SQLAlchemy 2.x here:
# Apache Airflow 3.0.1 requires SQLAlchemy < 2.0 for its metadata DB models.
COPY app /opt/airflow/app
RUN chown -R airflow:root /opt/airflow/app

# DAG processor may use `python -I` (no user site). Install into system site-packages.
# Use `python -m pip` as root: the `pip` entrypoint blocks root; module invocation does not.
RUN python -m pip install --no-cache-dir \
    "openpyxl==3.1.5" \
    "defusedxml==0.7.1" \
    "pydantic>=2.8.0,<3" \
    "pydantic-settings>=2.3.0,<3" \
    "asyncpg>=0.29.0,<1"

USER airflow
WORKDIR /opt/airflow

ENV PYTHONPATH=/opt/airflow
