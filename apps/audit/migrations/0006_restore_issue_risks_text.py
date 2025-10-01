from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('audit', '0004_remove_historicalissue_audit_procedures'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="ALTER TABLE audit_issue ADD COLUMN IF NOT EXISTS risks text NULL;",
                    reverse_sql="ALTER TABLE audit_issue DROP COLUMN IF EXISTS risks;",
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='issue',
                    name='risks',
                    field=models.TextField(blank=True, null=True, verbose_name='Risks'),
                ),
            ],
        ),
    ]


