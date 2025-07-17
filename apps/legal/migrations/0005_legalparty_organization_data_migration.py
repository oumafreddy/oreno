from django.db import migrations

def map_legalparty_organization(apps, schema_editor):
    LegalParty = apps.get_model('legal', 'LegalParty')
    Organization = apps.get_model('organizations', 'Organization')
    # Loop through all LegalParty records
    for party in LegalParty.objects.all():
        org = None
        # Try to match by name
        if party.organization and isinstance(party.organization, str):
            org = Organization.objects.filter(name=party.organization).first()
            # If not found by name, try by code
            if not org:
                org = Organization.objects.filter(code=party.organization).first()
        if org:
            party.organization_id = org.id
            party.save()
        else:
            # If no match, you can choose to set a default, skip, or log
            # For now, we skip and print a warning (will need manual fix)
            print(f"WARNING: No Organization found for LegalParty id={party.id} with old value '{party.organization}'")

class Migration(migrations.Migration):

    dependencies = [
        ('legal', '0004_alter_legalparty_organization'),
        ('organizations', '0002_initial'),  # adjust if your org migration is different
    ]

    operations = [
        migrations.RunPython(map_legalparty_organization, reverse_code=migrations.RunPython.noop),
    ]