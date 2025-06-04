from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):
    """
    This migration properly implements the fields from OrganizationOwnedModel and AuditableModel
    for the Notification model, ensuring compatibility with multi-tenant architecture.
    """

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('organizations', '0001_initial'),  # Update this if needed
        ('audit', '0003_notification_created_by_notification_updated_at_and_more'),
    ]

    operations = [
        # Explicitly add organization field with nullable=True initially
        migrations.AddField(
            model_name='notification',
            name='organization',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='notification_set',
                to='organizations.organization',
                verbose_name='organization'
            ),
        ),
        
        # Add created_by field 
        migrations.AddField(
            model_name='notification',
            name='created_by',
            field=models.ForeignKey(
                blank=True,
                help_text='User who created this record',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='notification_created',
                to=settings.AUTH_USER_MODEL,
                verbose_name='created by'
            ),
        ),
        
        # Add updated_by field
        migrations.AddField(
            model_name='notification',
            name='updated_by',
            field=models.ForeignKey(
                blank=True,
                help_text='User who last modified this record',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='notification_updated',
                to=settings.AUTH_USER_MODEL,
                verbose_name='updated by'
            ),
        ),
        
        # Add updated_at timestamp
        migrations.AddField(
            model_name='notification',
            name='updated_at',
            field=models.DateTimeField(
                auto_now=True,
                verbose_name='updated at'
            ),
        ),
    ]
