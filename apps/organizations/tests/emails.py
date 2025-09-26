from core.utils import send_tenant_email as send_mail

send_mail(
    'Test Subject',
    'This is a test message from Oreno GRC.',
    'info@oreno.tech',  # From email
    ['fredouma@oreno.tech'],  # To email(s)
    fail_silently=False,
)