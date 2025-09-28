# Generated manually for email preferences and logging features

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_add_password_expiration_period'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserEmailPreferences',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password_change_notifications', models.BooleanField(default=True, help_text='Receive email notifications when password is changed', verbose_name='Password Change Notifications')),
                ('password_expiry_warnings', models.BooleanField(default=True, help_text='Receive email warnings before password expires', verbose_name='Password Expiry Warnings')),
                ('password_expiry_notifications', models.BooleanField(default=True, help_text='Receive email notifications when password expires', verbose_name='Password Expiry Notifications')),
                ('security_alerts', models.BooleanField(default=True, help_text='Receive email alerts for security events', verbose_name='Security Alerts')),
                ('login_notifications', models.BooleanField(default=False, help_text='Receive email notifications for successful logins', verbose_name='Login Notifications')),
                ('suspicious_activity_alerts', models.BooleanField(default=True, help_text='Receive email alerts for suspicious account activity', verbose_name='Suspicious Activity Alerts')),
                ('account_locked_notifications', models.BooleanField(default=True, help_text='Receive email notifications when account is locked', verbose_name='Account Locked Notifications')),
                ('account_unlocked_notifications', models.BooleanField(default=True, help_text='Receive email notifications when account is unlocked', verbose_name='Account Unlocked Notifications')),
                ('system_maintenance_notifications', models.BooleanField(default=True, help_text='Receive email notifications about system maintenance', verbose_name='System Maintenance Notifications')),
                ('policy_update_notifications', models.BooleanField(default=True, help_text='Receive email notifications about policy updates', verbose_name='Policy Update Notifications')),
                ('notification_frequency', models.CharField(choices=[('immediate', 'Immediate'), ('daily', 'Daily Digest'), ('weekly', 'Weekly Digest'), ('disabled', 'Disabled')], default='immediate', help_text='How often to receive non-critical notifications', max_length=20, verbose_name='Notification Frequency')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=models.deletion.CASCADE, related_name='email_preferences', to='users.customuser', verbose_name='User')),
            ],
            options={
                'verbose_name': 'User Email Preferences',
                'verbose_name_plural': 'User Email Preferences',
            },
        ),
        migrations.CreateModel(
            name='EmailLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email_type', models.CharField(choices=[('password_change', 'Password Change Notification'), ('password_expiry_warning', 'Password Expiry Warning'), ('password_expiry', 'Password Expiry Notification'), ('security_alert', 'Security Alert'), ('login_notification', 'Login Notification'), ('account_locked', 'Account Locked Notification'), ('account_unlocked', 'Account Unlocked Notification'), ('system_maintenance', 'System Maintenance Notification'), ('policy_update', 'Policy Update Notification'), ('welcome', 'Welcome Email'), ('otp', 'OTP Email'), ('marketing', 'Marketing Email')], max_length=50, verbose_name='Email Type')),
                ('recipient_email', models.EmailField(verbose_name='Recipient Email')),
                ('subject', models.CharField(max_length=255, verbose_name='Email Subject')),
                ('status', models.CharField(choices=[('sent', 'Sent Successfully'), ('failed', 'Failed to Send'), ('skipped', 'Skipped (User Preference)'), ('pending', 'Pending')], default='pending', max_length=20, verbose_name='Status')),
                ('error_message', models.TextField(blank=True, help_text='Error details if email failed to send', null=True, verbose_name='Error Message')),
                ('sent_at', models.DateTimeField(blank=True, null=True, verbose_name='Sent At')),
                ('ip_address', models.GenericIPAddressField(blank=True, help_text='IP address from which the action was triggered', null=True, verbose_name='IP Address')),
                ('user_agent', models.TextField(blank=True, help_text='User agent string from the request', null=True, verbose_name='User Agent')),
                ('context_data', models.JSONField(blank=True, default=dict, help_text='Additional context data for the email', verbose_name='Context Data')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, related_name='email_logs', to='users.customuser', verbose_name='User')),
            ],
            options={
                'verbose_name': 'Email Log',
                'verbose_name_plural': 'Email Logs',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='emaillog',
            index=models.Index(fields=['user', 'email_type'], name='users_emai_user_id_4a8b8a_idx'),
        ),
        migrations.AddIndex(
            model_name='emaillog',
            index=models.Index(fields=['recipient_email', 'status'], name='users_emai_recipie_8b2b1a_idx'),
        ),
        migrations.AddIndex(
            model_name='emaillog',
            index=models.Index(fields=['created_at'], name='users_emai_created_9b2b1a_idx'),
        ),
        migrations.AddIndex(
            model_name='emaillog',
            index=models.Index(fields=['status'], name='users_emai_status_9b2b1a_idx'),
        ),
    ]
