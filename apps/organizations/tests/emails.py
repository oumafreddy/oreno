from django.core.mail import send_mail

send_mail(
    'Test Subject',
    'This is a test message from Oreno GRC.',
    'info@oreno.tech',  # From email
    ['fredouma@oreno.tech'],  # To email(s)
    fail_silently=False,
)