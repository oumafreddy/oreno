from django.db import migrations
from django.utils import timezone
from django.utils.crypto import get_random_string

def create_default_riskregister(apps, schema_editor):
    Organization = apps.get_model('organizations', 'Organization')
    User = apps.get_model('users', 'CustomUser')
    RiskRegister = apps.get_model('risk', 'RiskRegister')
    db_alias = schema_editor.connection.alias

    # Try to get by code, then by schema_name, then by name
    org = None
    try:
        org = Organization.objects.using(db_alias).get(code='org001')
    except Organization.DoesNotExist:
        try:
            org = Organization.objects.using(db_alias).get(schema_name='org001')
        except Organization.DoesNotExist:
            try:
                org = Organization.objects.using(db_alias).get(name='Organization 001')
            except Organization.DoesNotExist:
                # As a last resort, create a new org with a unique schema_name
                org = Organization.objects.using(db_alias).create(
                    code='org001',
                    name='Organization 001',
                    schema_name='org001_' + get_random_string(5),
                )

    # Fetch or create the user
    try:
        user = User.objects.using(db_alias).get(email='xawomek648@astimei.com')
    except User.DoesNotExist:
        user = User.objects.using(db_alias).create(
            email='xawomek648@astimei.com',
            username='defaultuser',
            organization=org,
        )

    if not RiskRegister.objects.using(db_alias).filter(id=1).exists():
        RiskRegister.objects.using(db_alias).create(
            id=1,
            code='DEFAULT',
            register_name='Default Register',
            register_period='0000',
            register_description='Auto-created default register for risk assignment.',
            register_creation_date=timezone.now(),
            organization=org,
            created_by=user,
            updated_by=user,
        )

class Migration(migrations.Migration):
    dependencies = [
        ('risk', '0002_control_kri_riskassessment_riskcontrol_and_more'),
    ]
    operations = [
        migrations.RunPython(create_default_riskregister),
    ] 