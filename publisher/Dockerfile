# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3-slim

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install pip requirements
COPY requirements.txt .
RUN pip install --upgrade --no-cache-dir -r requirements.txt

# Instalar el agente de New Relic
RUN pip install --no-cache-dir newrelic

WORKDIR /app
COPY . /app

# Copiar archivo newrelic.ini
COPY newrelic.ini /publisher/newrelic.ini

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

# Comando de inicio con New Relic
CMD ["sh", "-c", "NEW_RELIC_CONFIG_FILE=newrelic.ini newrelic-admin run-program fastapi run main.py --port 7999"]