from django.shortcuts import render
from django.http import JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.core.cache import cache


def service_paused(request):
    return render(request, 'service_paused.html') 


@csrf_exempt
def public_contact_submit(request: HttpRequest):
    """Accepts contact form submissions and emails info@oreno.tech.

    Expects POST form or JSON with fields: name, email, subject, message.
    Returns JSON {success: true} on success.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    # Support both form-encoded and JSON bodies
    name = request.POST.get('name') or ''
    email = request.POST.get('email') or ''
    subject = request.POST.get('subject') or ''
    message = request.POST.get('message') or ''
    honeypot = request.POST.get('company') or ''
    form_ts = request.POST.get('form_ts') or ''

    if not (name and email and subject and message):
        try:
            import json as _json
            data = _json.loads(request.body or b'{}')
            name = name or data.get('name', '')
            email = email or data.get('email', '')
            subject = subject or data.get('subject', '')
            message = message or data.get('message', '')
            honeypot = honeypot or data.get('company', '')
            form_ts = form_ts or data.get('form_ts', '')
        except Exception:
            pass

    if not (name and email and subject and message):
        return JsonResponse({'success': False, 'error': 'Missing required fields'}, status=400)

    # Spam: honeypot should be empty
    if honeypot:
        return JsonResponse({'success': True})  # Pretend success

    # Spam: timing check (at least 3 seconds from render to submit)
    try:
        import time as _time
        ts = int(form_ts)
        if ts > 0 and (_time.time() - ts) < 3:
            return JsonResponse({'success': True})  # Pretend success
    except Exception:
        pass

    # Rate limiting per IP: 5 requests per hour
    ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or request.META.get('REMOTE_ADDR', '')
    rl_key = f"contact_rate:{ip}"
    try:
        count = cache.get(rl_key, 0)
        if count >= 5:
            return JsonResponse({'success': False, 'error': 'Rate limit exceeded. Please try again later.'}, status=429)
        cache.set(rl_key, count + 1, 3600)
    except Exception:
        pass

    to_email = getattr(settings, 'PUBLIC_CONTACT_EMAIL', 'info@oreno.tech')
    mail_subject = f"[Oreno Contact] {subject}"
    text_body = (
        f"New contact form submission\n\n"
        f"From: {name} <{email}>\n"
        f"Subject: {subject}\n\n"
        f"Message:\n{message}\n"
    )

    html_body = (
        "<div style=\"font-family:Arial,Helvetica,sans-serif;line-height:1.6;color:#222\">"
        f"<h2 style=\"margin:0 0 12px\">New Contact Message</h2>"
        f"<p><strong>From:</strong> {name} &lt;{email}&gt;</p>"
        f"<p><strong>Subject:</strong> {subject}</p>"
        f"<div style=\"margin-top:12px;padding:12px;border-left:4px solid #0052cc;background:#f6f8fa;border-radius:6px\">{message.replace('<','&lt;').replace('>','&gt;').replace('\n','<br>')}</div>"
        "</div>"
    )

    try:
        msg = EmailMultiAlternatives(
            subject=mail_subject,
            body=text_body,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@oreno.tech'),
            to=[to_email],
        )
        msg.attach_alternative(html_body, "text/html")
        msg.send(fail_silently=False)
    except Exception as exc:
        return JsonResponse({'success': False, 'error': str(exc)}, status=500)

    return JsonResponse({'success': True})