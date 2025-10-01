from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('audit', '0008_alter_historicalissue_risks'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalissue',
            name='risks',
            field=models.TextField(blank=True, null=True, verbose_name='Risks'),
        ),
    ]


