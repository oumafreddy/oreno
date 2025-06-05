from django_tenants.utils import get_public_schema_name
from django_tenants.utils import get_tenant_model
import functools

class SafeTenantProxy:
    def __init__(self, tenant=None):
        self._tenant = tenant
        self._schema_name = getattr(tenant, 'schema_name', get_public_schema_name())
    
    def __getattr__(self, name):
        if self._tenant is not None and hasattr(self._tenant, name):
            return getattr(self._tenant, name)
        if name == 'schema_name':
            return self._schema_name
        raise AttributeError(f"'SafeTenantProxy' has no attribute '{name}'")

class AdminTenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.public_schema_name = get_public_schema_name()
        
        # Let's wrap the original template tag function to debug it
        try:
            from django_tenants.templatetags import tenant
            original_is_public_schema = tenant.is_public_schema
            
            @functools.wraps(original_is_public_schema)
            def debug_is_public_schema(context, app):
                try:
                    # Check if request is present
                    has_request = hasattr(context, 'request')
                    if not has_request:
                        print("DEBUG: Template context has no request")
                        return True
                    
                    # Check if tenant is present
                    has_tenant = hasattr(context.request, 'tenant')
                    tenant = getattr(context.request, 'tenant', None) 
                    if not has_tenant or tenant is None:
                        print("DEBUG: Request has no tenant")
                        return True
                    
                    # Print info about the tenant
                    schema_name = getattr(tenant, 'schema_name', None)
                    print(f"DEBUG: Request tenant schema_name: {schema_name}")
                    if schema_name is None:
                        print("DEBUG: Tenant has no schema_name")
                        return True
                    
                    result = schema_name == get_public_schema_name()
                    print(f"DEBUG: is_public_schema result: {result}")
                    return result
                except Exception as e:
                    print(f"DEBUG: Error in is_public_schema: {e}")
                    return True
            
            # Replace the original
            tenant.is_public_schema = debug_is_public_schema
            print("Patched is_public_schema with debug version")
        except Exception as e:
            print(f"Failed to patch is_public_schema: {e}")
    
    def __call__(self, request):
        # Process only admin requests
        if request.path.startswith('/admin/'):
            print(f"AdminTenantMiddleware: Processing admin request: {request.path}")
            
            # Get tenant from request
            tenant_before = getattr(request, 'tenant', None)
            schema_before = getattr(tenant_before, 'schema_name', None)
            print(f"AdminTenantMiddleware: Before - tenant: {tenant_before}, schema: {schema_before}")
            
            # Set our safe tenant
            if tenant_before is None:
                try:
                    # Try to get the public tenant
                    TenantModel = get_tenant_model()
                    public_tenant = TenantModel.objects.get(schema_name=self.public_schema_name)
                    print(f"AdminTenantMiddleware: Setting public tenant: {public_tenant}")
                    request.tenant = public_tenant
                except Exception as e:
                    print(f"AdminTenantMiddleware: Error getting public tenant: {e}")
                    request.tenant = SafeTenantProxy(None)
            else:
                # Add safety wrapper
                request.tenant = SafeTenantProxy(tenant_before)
            
            print(f"AdminTenantMiddleware: After - tenant: {request.tenant}, schema: {getattr(request.tenant, 'schema_name', None)}")
            
            # Save our middleware as a request attribute
            request._admin_tenant_middleware = self
        
        # Process the request
        response = self.get_response(request)
        
        # Check tenant after response
        if request.path.startswith('/admin/'):
            tenant_after = getattr(request, 'tenant', None)
            schema_after = getattr(tenant_after, 'schema_name', None)
            print(f"AdminTenantMiddleware: After response - tenant: {tenant_after}, schema: {schema_after}")
        
        return response