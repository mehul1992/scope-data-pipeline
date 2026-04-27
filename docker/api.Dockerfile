FROM python:3.11-slim

WORKDIR /workspace

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY app /workspace/app
COPY pyproject.toml README.md /workspace/
COPY docker/entrypoint.sh /workspace/entrypoint.sh
COPY alembic.ini /workspace/alembic.ini
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir .

# RUN alembic upgrade head
RUN chmod +x /workspace/entrypoint.sh

ENTRYPOINT ["/workspace/entrypoint.sh"]
