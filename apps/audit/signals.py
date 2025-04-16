# audits/signals.py
@receiver(post_save, sender=Approval)
def log_approval_metrics(sender, instance, **kwargs):
    metrics.incr(f'approval.{instance.status}')
    timing_key = f'approval_time.{instance.content_type.model}'
    metrics.timing(timing_key, instance.updated_at - instance.created_at)