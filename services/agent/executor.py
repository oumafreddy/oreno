from django_tenants.utils import tenant_context
from rest_framework.exceptions import ValidationError

# Import target serializers
from audit.serializers import AuditWorkplanSerializer  # type: ignore[reportMissingImports]
from risk.serializers import RiskSerializer, RiskRegisterSerializer  # type: ignore[reportMissingImports]
from compliance.serializers import ComplianceFrameworkSerializer  # type: ignore[reportMissingImports]

class AgentExecutor:
    def __init__(self, request):
        self.request = request
        self.tenant = getattr(request, 'tenant', None)
        self.user = request.user

    def execute(self, intent: dict) -> dict:
        action = intent.get('action')
        model = intent.get('model')
        fields = intent.get('fields') or {}
        if not self.tenant:
            raise ValidationError({'detail': 'Tenant context missing'})
        with tenant_context(self.tenant):
            if action == 'create' and model == 'audit.AuditWorkplan':
                return self._create_audit_workplan(fields)
            if action == 'create' and model == 'risk.Risk':
                return self._create_risk(fields)
            if action == 'create' and model == 'compliance.ComplianceFramework':
                return self._create_compliance_framework(fields)
        raise ValidationError({'detail': f'Unsupported intent: {action} {model}'})

    def _inject_org(self, fields: dict) -> dict:
        if 'organization' not in fields and hasattr(self.user, 'organization') and self.user.organization:
            fields = dict(fields)
            fields['organization'] = self.user.organization_id
        return fields

    def _create_audit_workplan(self, fields: dict) -> dict:
        # Map incoming intent fields to serializer fields and avoid passing
        # organization so the serializer assigns from request.user.
        mapped = {}
        if 'code' in fields:
            mapped['code'] = fields['code']
        if 'title' in fields:
            mapped['name'] = fields['title']
        if 'year' in fields:
            mapped['fiscal_year'] = fields['year']
        if 'description' in fields:
            mapped['description'] = fields['description']
        if 'status' in fields:
            mapped['state'] = fields['status']
        # ignore unknowns like 'origin'

        serializer = AuditWorkplanSerializer(data=mapped, context={'request': self.request})
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return {'model': 'audit.AuditWorkplan', 'id': obj.id, 'url': f'/audit/workplans/{obj.id}/'}

    def _create_risk(self, fields: dict) -> dict:
        fields = self._inject_org(fields)
        serializer = RiskSerializer(data=fields, context={'request': self.request})
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return {'model': 'risk.Risk', 'id': obj.id, 'url': f'/risk/risks/{obj.id}/'}

    def _create_compliance_framework(self, fields: dict) -> dict:
        fields = self._inject_org(fields)
        serializer = ComplianceFrameworkSerializer(data=fields, context={'request': self.request})
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return {'model': 'compliance.ComplianceFramework', 'id': obj.id, 'url': f'/compliance/frameworks/{obj.id}/'}
