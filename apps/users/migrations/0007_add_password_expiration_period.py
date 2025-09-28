# Generated manually for password expiration period feature

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_alter_customuser_role_alter_organizationrole_role_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='password_expiration_period',
            field=models.CharField(
                choices=[
                    ('never', 'Never expires'),
                    ('monthly', 'Monthly (30 days)'),
                    ('3_months', '3 months (90 days)'),
                    ('6_months', '6 months (180 days)'),
                    ('1_year', '1 year (365 days)')
                ],
                default='3_months',
                help_text='How often this user\'s password should expire. This setting overrides organization policy.',
                max_length=20,
                verbose_name='Password Expiration Period'
            ),
        ),
    ]