from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('audit', '0004_remove_historicalissue_audit_procedures'),
    ]

    operations = [
        migrations.AddField(
            model_name='issue',
            name='risks',
            field=models.TextField(blank=True, null=True, verbose_name='Risks'),
        ),
    ]


