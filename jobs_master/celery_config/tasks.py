# celery
from celery import shared_task

# The "shared_task" decorator allows creation
# of Celery tasks for reusable apps as it doesn't
# need the instance of the Celery app.
# @celery_app.task()

# TODO: replace with actual tasks

@shared_task
def get_user_purchases(user_id):
    compras = [
        {'team_id': 1, 'resultado': 'win'},
        {'team_id': 2, 'resultado': 'loss'}
    ]
    return compras

@shared_task
def get_future_matches(teams):
    partidos = [
        {'partido_id': 1, 'team_id': 1, 'liga': 'Premier League'},
        {'partido_id': 2, 'team_id': 2, 'liga': 'La Liga'}
    ]
    return partidos

@shared_task
def calculate_historical_accuracies(user_id, teams):
    aciertos = {1: 5, 2: 3}
    return aciertos

@shared_task
def calculate_league_benefits(accuracies, matches):
    beneficios = []
    for partido in matches:
        equipo_id = partido['team_id']
        acierto = accuracies.get(equipo_id, 0)
        round_de_liga = partido.get('round', 1)
        odd_de_equipo = partido.get('odd', 1.5)
        ponderador = (acierto * round_de_liga) / odd_de_equipo
        beneficios.append({'partido_id': partido['partido_id'], 'ponderador': ponderador})
    return sorted(beneficios, key=lambda x: x['ponderador'], reverse=True)

@shared_task
def get_top_matches(benefits):
    return benefits[:3]

@shared_task
def process_webpay_payment(user_id, deposit_token):
    success = True
    return {'success': success}

@shared_task
def send_validation_result(payment_status, top_matches):
    return {'status': payment_status, 'recommended_matches': top_matches}