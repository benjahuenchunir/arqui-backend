# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3-slim

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install pip requirements
COPY api/requirements.txt .
RUN pip install --upgrade --no-cache-dir -r requirements.txt

# Install New Relic
RUN pip install newrelic

WORKDIR /api
COPY api/app /api/app
COPY db /api/db

# Copy New Relic configuration (assuming newrelic.ini is in the api directory)
COPY api/newrelic.ini /api/newrelic.ini

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /api/app
USER appuser

#Código para el Newrelic, medida de metricas
CMD ["sh", "-c", "NEW_RELIC_CONFIG_FILE=newrelic.ini newrelic-admin run-program uvicorn app.main:app --host 0.0.0.0 --port 8000"]