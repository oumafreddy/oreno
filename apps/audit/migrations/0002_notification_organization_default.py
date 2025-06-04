from django.db import migrations

# This is an empty migration that matches the database record
# It's meant to reconcile migration history after manual model changes

class Migration(migrations.Migration):

    dependencies = [
        ('audit', '0001_initial'),
    ]

    operations = [
        # Empty - we just need the file to match what's in the database
    ]
