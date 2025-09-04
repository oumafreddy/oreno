from celery import shared_task


@shared_task
def noop_ai_governance_task():
    return 'ok'
