from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('audit', '0018_add_engagement_document'),
    ]

    operations = [
        migrations.RunSQL(
            sql="DROP TABLE IF EXISTS audit_procedureresult CASCADE;",
            reverse_sql="",
        ),
    ]
