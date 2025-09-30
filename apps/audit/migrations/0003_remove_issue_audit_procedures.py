from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('audit', '0002_alter_auditworkplan_description_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='issue',
            name='audit_procedures',
        ),
    ]



