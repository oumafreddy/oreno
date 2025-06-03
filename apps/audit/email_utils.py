from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

# All email notification functions moved here

def send_workplan_approval_notification(workplan, status, request):
    """
    Send email notification for workplan approval status changes.
    Implementation moved from utils.py
    """
    # Function implementation...
    pass

def send_engagement_approval_notification(engagement, status, request):
    """
    Send email notification for engagement approval status changes.
    Implementation moved from utils.py
    """
    # Function implementation...
    pass
