FROM python:3.11-slim

WORKDIR /workspace

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY app /workspace/app
COPY pyproject.toml README.md /workspace/
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir .

# RUN alembic upgrade head

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
