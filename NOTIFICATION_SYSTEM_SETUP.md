# Intelligent Notification System Setup Guide

## Overview

This document provides setup instructions for the intelligent email notification system that automatically sends reminders and alerts for:

1. **Compliance Obligations**: 7-day reminders and 1-day overdue alerts
2. **Contract Milestones**: 7-day reminders and 1-day overdue alerts

## Features

- ✅ **Multi-tenant Support**: Emails are sent using organization-specific SMTP settings
- ✅ **Beautiful HTML Templates**: Professional, responsive email designs
- ✅ **Intelligent Owner Detection**: Automatically finds the right email recipient
- ✅ **Celery Integration**: Asynchronous email processing for better performance
- ✅ **Comprehensive Logging**: Full audit trail of all notifications sent
- ✅ **Dry Run Mode**: Test notifications without actually sending emails

## System Architecture

### Email Templates
- `templates/compliance/emails/obligation_due_reminder.html`
- `templates/compliance/emails/obligation_overdue_alert.html`
- `templates/contracts/emails/milestone_due_reminder.html`
- `templates/contracts/emails/milestone_overdue_alert.html`

### Celery Tasks
- `apps/compliance/tasks.py` - Compliance obligation notifications
- `apps/contracts/tasks.py` - Contract milestone notifications

### Management Commands
- `python manage.py send_obligation_notifications` - Compliance only
- `python manage.py send_milestone_notifications` - Contracts only
- `python manage.py send_all_notifications` - Both systems

## Setup Instructions

### 1. Prerequisites

Ensure the following are properly configured:

- ✅ Celery worker is running
- ✅ Redis/RabbitMQ broker is configured
- ✅ Email settings are configured in Django settings
- ✅ Multi-tenant email settings are configured (if using per-tenant SMTP)

### 2. Test the System

Before setting up cron jobs, test the system:

```bash
# Test compliance obligations (dry run)
python manage.py send_obligation_notifications --dry-run

# Test contract milestones (dry run)
python manage.py send_milestone_notifications --dry-run

# Test both systems (dry run)
python manage.py send_all_notifications --dry-run
```

### 3. Manual Testing

Send a test notification:

```bash
# Send actual notifications (remove --dry-run)
python manage.py send_all_notifications
```

### 4. Cron Job Setup

#### Option A: Daily Check (Recommended)

Add to your crontab (`crontab -e`):

```bash
# Run daily at 9:00 AM
0 9 * * * cd /path/to/oreno && /path/to/venv/bin/python manage.py send_all_notifications >> /var/log/oreno/notifications.log 2>&1
```

#### Option B: Separate Cron Jobs

```bash
# Compliance obligations - daily at 9:00 AM
0 9 * * * cd /path/to/oreno && /path/to/venv/bin/python manage.py send_obligation_notifications >> /var/log/oreno/compliance_notifications.log 2>&1

# Contract milestones - daily at 9:30 AM
30 9 * * * cd /path/to/oreno && /path/to/venv/bin/python manage.py send_milestone_notifications >> /var/log/oreno/contract_notifications.log 2>&1
```

#### Option C: Multiple Daily Checks

```bash
# Morning check at 9:00 AM
0 9 * * * cd /path/to/oreno && /path/to/venv/bin/python manage.py send_all_notifications >> /var/log/oreno/notifications_morning.log 2>&1

# Afternoon check at 2:00 PM
0 14 * * * cd /path/to/oreno && /path/to/venv/bin/python manage.py send_all_notifications >> /var/log/oreno/notifications_afternoon.log 2>&1
```

### 5. Logging Setup

Create log directories and configure logging:

```bash
# Create log directory
sudo mkdir -p /var/log/oreno
sudo chown your_user:your_group /var/log/oreno

# Add to Django settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'notification_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/oreno/notifications.log',
        },
    },
    'loggers': {
        'compliance.tasks': {
            'handlers': ['notification_file'],
            'level': 'INFO',
            'propagate': True,
        },
        'contracts.tasks': {
            'handlers': ['notification_file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

## How It Works

### Compliance Obligations

1. **Due Reminders (7 days before)**:
   - Finds obligations due in exactly 7 days
   - Sends to `owner.email` or `owner_email` field
   - Uses `obligation_due_reminder.html` template

2. **Overdue Alerts (1 day after)**:
   - Finds obligations overdue by exactly 1 day
   - Sends to `owner.email` or `owner_email` field
   - Uses `obligation_overdue_alert.html` template

### Contract Milestones

1. **Due Reminders (7 days before)**:
   - Finds milestones due in exactly 7 days
   - Sends to primary party's `contact_email` or any party with email
   - Uses `milestone_due_reminder.html` template

2. **Overdue Alerts (1 day after)**:
   - Finds milestones overdue by exactly 1 day
   - Sends to primary party's `contact_email` or any party with email
   - Uses `milestone_overdue_alert.html` template

## Email Recipient Logic

### Compliance Obligations
```python
if obligation.owner:
    recipient_email = obligation.owner.email
    owner_name = obligation.owner.get_full_name() or obligation.owner.email
elif obligation.owner_email:
    recipient_email = obligation.owner_email
    owner_name = obligation.owner_email
```

### Contract Milestones
```python
# Try primary party first
primary_party = milestone.contract.parties.filter(
    contractparty__is_primary_party=True
).first()

if primary_party and primary_party.contact_email:
    recipient_email = primary_party.contact_email
    owner_name = primary_party.contact_person or primary_party.name
else:
    # Fallback to any party with email
    party_with_email = milestone.contract.parties.filter(
        contact_email__isnull=False
    ).exclude(contact_email='').first()
```

## Monitoring and Maintenance

### Check Logs
```bash
# View recent notifications
tail -f /var/log/oreno/notifications.log

# Check for errors
grep -i error /var/log/oreno/notifications.log
```

### Test Individual Notifications
```bash
# Test specific obligation
python manage.py shell
>>> from compliance.tasks import send_obligation_due_reminder
>>> send_obligation_due_reminder.delay(obligation_id=1, organization_id=1)

# Test specific milestone
>>> from contracts.tasks import send_milestone_due_reminder
>>> send_milestone_due_reminder.delay(milestone_id=1, organization_id=1)
```

### Monitor Celery Tasks
```bash
# Check Celery worker status
celery -A config worker --loglevel=info

# Monitor task queue
celery -A config inspect active
```

## Troubleshooting

### Common Issues

1. **No emails being sent**:
   - Check Celery worker is running
   - Verify email settings in Django
   - Check logs for errors

2. **Wrong recipients**:
   - Verify owner fields are populated
   - Check contact_email fields for contracts
   - Review recipient logic in tasks

3. **Template errors**:
   - Check template syntax
   - Verify template paths
   - Test with dry-run mode

### Debug Mode

Enable debug logging:

```python
# In Django settings
LOGGING['loggers']['compliance.tasks']['level'] = 'DEBUG'
LOGGING['loggers']['contracts.tasks']['level'] = 'DEBUG'
```

## Security Considerations

- ✅ **Multi-tenant Isolation**: Each organization's emails use their own SMTP settings
- ✅ **Email Validation**: Recipients are validated before sending
- ✅ **Error Handling**: Failed emails are logged but don't crash the system
- ✅ **Rate Limiting**: Celery provides built-in rate limiting
- ✅ **Audit Trail**: All notifications are logged with timestamps

## Performance Optimization

- ✅ **Asynchronous Processing**: All emails are sent via Celery
- ✅ **Batch Processing**: Multiple notifications are processed efficiently
- ✅ **Database Optimization**: Uses select_related for efficient queries
- ✅ **Error Recovery**: Failed tasks can be retried automatically

## Future Enhancements

Potential improvements for future versions:

1. **Customizable Reminder Periods**: Allow organizations to set custom reminder periods
2. **Escalation Rules**: Send notifications to managers if owners don't respond
3. **Email Preferences**: Allow users to opt-out of certain notification types
4. **SMS Notifications**: Add SMS support for critical alerts
5. **Dashboard Integration**: Show notification status in the dashboard
6. **Analytics**: Track notification effectiveness and response rates

## Support

For issues or questions:

1. Check the logs first: `/var/log/oreno/notifications.log`
2. Test with dry-run mode: `--dry-run`
3. Verify Celery worker is running
4. Check email configuration
5. Review recipient data in the database

---

**Note**: This system is designed to be production-ready and follows enterprise-grade practices for reliability, security, and maintainability.
