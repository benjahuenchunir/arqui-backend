import os

from celery import Celery

if os.getenv("ENV") != "production":
    from dotenv import load_dotenv

    load_dotenv()

# Inicializa New Relic
from newrelic import agent
agent.initialize('/newrelic.ini')  # Ajusta la ruta si es necesario

celery_app = Celery(
    __name__,
    # https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/index.html
    broker=os.environ.get('CELERY_BROKER_URL', ''),
    backend=os.environ.get('CELERY_RESULT_BACKEND', '')
)

# Setup to use all the variables in settings
# that begins with 'CELERY_'
celery_app.config_from_object('celery_config.config', namespace='CELERY')

# Habilitar instrumentación de tareas (opcional)
from newrelic.agent import register_application, current_transaction

# Registrar la aplicación en New Relic (opcional)
register_application(timeout=10.0)

# Decorador para instrumentar manualmente una tarea
@celery_app.task(name="example_task")
def example_task(param):
    transaction = current_transaction()
    if transaction:
        transaction.add_custom_parameter("task_param", param)
    print(f"Processing: {param}")
    return f"Processed {param}"