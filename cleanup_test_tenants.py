"""
Script to clean up test tenant schemas created by pytest.
These tenant_a_* and tenant_b_* schemas were created during test runs
but not properly cleaned up.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from organizations.models import Organization, Domain  # type: ignore[reportMissingImports]
from django.db import connection

def cleanup_test_tenants():
    """Remove all test tenant schemas and organizations"""
    test_prefixes = ['tenant_a_', 'tenant_b_']
    
    # Find all test organizations
    test_orgs = Organization.objects.filter(
        schema_name__startswith='tenant_a_'
    ) | Organization.objects.filter(
        schema_name__startswith='tenant_b_'
    )
    
    print(f"Found {test_orgs.count()} test organizations to clean up")
    
    for org in test_orgs:
        print(f"  Removing {org.schema_name} - {org.name}")
        
        # Delete associated domains first
        Domain.objects.filter(tenant=org).delete()
        
        # Drop the schema
        try:
            with connection.cursor() as cursor:
                cursor.execute(f'DROP SCHEMA IF EXISTS "{org.schema_name}" CASCADE')
            print(f"    [OK] Dropped schema {org.schema_name}")
        except Exception as e:
            print(f"    [ERROR] Error dropping schema: {e}")
        
        # Delete the organization (skip foreign key checks since schema is dropped)
        try:
            org.delete()
            print(f"    [OK] Deleted organization record")
        except Exception as e:
            # If deletion fails due to foreign key constraints, force delete
            print(f"    [WARNING] Standard delete failed: {e}")
            try:
                # Use raw SQL to delete the organization record
                with connection.cursor() as cursor:
                    cursor.execute('DELETE FROM organizations_organization WHERE id = %s', [org.id])
                print(f"    [OK] Force deleted organization record")
            except Exception as e2:
                print(f"    [ERROR] Force delete also failed: {e2}")
    
    print(f"\nCleanup complete! Removed {test_orgs.count()} test tenants.")

if __name__ == '__main__':
    cleanup_test_tenants()

