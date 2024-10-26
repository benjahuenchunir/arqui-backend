# celery

# https://docs.celeryq.dev/en/3.1/configuration.html
accept_content = ['application/json']
CELERY_SERIALIZER = 'json'
result_serializer = 'json'
# Configure Celery to use a custom time zone.
timezone = 'America/Santiago'
# A sequence of modules to import when the worker starts
imports = ('celery_config.tasks', )