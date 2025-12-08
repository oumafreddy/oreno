import importlib
from typing import Dict, Any

from django.apps import apps
from django_tenants.utils import tenant_context
from rest_framework.exceptions import ValidationError

from services.agent.schema_index import get_schema_index


class AgentExecutor:
    """
    Universal executor that uses the schema index to dynamically perform CRUD
    across all indexed models. Security guardrails:
    - Requires tenant context
    - Organization injection + isolation
    - Serializer-first validation
    - Respects read-only fields
    """

    def __init__(self, request):
        self.request = request
        self.tenant = getattr(request, 'tenant', None)
        self.user = request.user
        self.schema_index = get_schema_index()

    def execute(self, intent: dict, preview: bool = False) -> dict:
        action = intent.get('action')
        model_path = intent.get('model')
        fields = intent.get('fields') or {}
        obj_id = intent.get('id')
        filters = intent.get('filters') or {}

        if not self.tenant:
            raise ValidationError({'detail': 'Tenant context missing'})
        if not model_path:
            raise ValidationError({'detail': 'Model is required'})

        model_schema = self.schema_index.get_model_schema(model_path)
        if not model_schema:
            raise ValidationError({'detail': f'Model not supported: {model_path}'})

        self._check_permissions(action, model_path)

        with tenant_context(self.tenant):
            if action == 'create':
                return self._create(model_path, model_schema, fields, preview=preview)
            if action == 'update':
                return self._update(model_path, model_schema, obj_id, fields, preview=preview)
            if action == 'delete':
                return self._delete(model_path, model_schema, obj_id, preview=preview)
            if action == 'read':
                return self._read(model_path, model_schema, filters)

        raise ValidationError({'detail': f'Unsupported intent: {action} {model_path}'})

    # ------------------------------------------------------------------ #
    # Core CRUD operations
    # ------------------------------------------------------------------ #
    def _create(self, model_path: str, schema: Dict[str, Any], fields: Dict[str, Any], preview: bool) -> dict:
        model_cls = self._get_model_class(model_path)
        serializer_cls = self._get_serializer_class(schema)

        mapped = self._map_fields(fields, schema)
        mapped, warnings = self._strip_read_only(mapped, schema)
        mapped = self._resolve_relationships(mapped, schema)
        mapped = self._inject_org_if_needed(mapped, schema)
        serializer = serializer_cls(data=mapped, context={'request': self.request})
        serializer.is_valid(raise_exception=True)
        if preview:
            return {
                'model': model_path,
                'action': 'create',
                'preview': True,
                'data': serializer.validated_data,
                'warnings': warnings,
                'missing_required': self._missing_required_fields(mapped, schema),
            }
        obj = serializer.save()
        self._audit('agent_create', model_path, obj.id, mapped)
        return {'model': model_path, 'id': obj.id}

    def _update(self, model_path: str, schema: Dict[str, Any], obj_id: Any, fields: Dict[str, Any], preview: bool) -> dict:
        if not obj_id:
            raise ValidationError({'detail': 'id is required for update'})
        model_cls = self._get_model_class(model_path)
        serializer_cls = self._get_serializer_class(schema)

        mapped = self._map_fields(fields, schema)
        mapped, warnings = self._strip_read_only(mapped, schema)
        mapped = self._resolve_relationships(mapped, schema)
        mapped = self._inject_org_if_needed(mapped, schema)
        try:
            obj = model_cls.objects.get(id=obj_id)
        except model_cls.DoesNotExist:
            raise ValidationError({'detail': f'Object not found: {model_path} id={obj_id}'})

        serializer = serializer_cls(obj, data=mapped, partial=True, context={'request': self.request})
        serializer.is_valid(raise_exception=True)
        if preview:
            # provide a simple diff: fields that would change
            changes = {}
            for k, v in serializer.validated_data.items():
                current = getattr(obj, k, None)
                if current != v:
                    changes[k] = {'from': current, 'to': v}
            return {
                'model': model_path,
                'action': 'update',
                'id': obj_id,
                'preview': True,
                'changes': changes,
                'warnings': warnings,
                'missing_required': self._missing_required_fields(mapped, schema),
            }
        obj = serializer.save()
        self._audit('agent_update', model_path, obj.id, mapped)
        return {'model': model_path, 'id': obj.id}

    def _delete(self, model_path: str, schema: Dict[str, Any], obj_id: Any, preview: bool) -> dict:
        if not obj_id:
            raise ValidationError({'detail': 'id is required for delete'})
        model_cls = self._get_model_class(model_path)
        exists = model_cls.objects.filter(id=obj_id).exists()
        if not exists:
            raise ValidationError({'detail': f'Object not found: {model_path} id={obj_id}'})
        if preview:
            return {'model': model_path, 'action': 'delete', 'id': obj_id, 'preview': True, 'exists': True}
        deleted, _ = model_cls.objects.filter(id=obj_id).delete()
        if deleted:
            self._audit('agent_delete', model_path, obj_id, {})
        return {'model': model_path, 'id': obj_id, 'deleted': True}

    def _read(self, model_path: str, schema: Dict[str, Any], filters: Dict[str, Any]) -> dict:
        model_cls = self._get_model_class(model_path)
        qs = model_cls.objects.all()

        # Organization scoping when applicable
        if 'organization' in schema.get('fields', {}) and hasattr(self.user, 'organization') and self.user.organization_id:
            qs = qs.filter(organization_id=self.user.organization_id)

        # Apply simple filters
        safe_filters = {}
        for key, value in (filters or {}).items():
            if key in schema.get('fields', {}):
                safe_filters[key] = value
        if safe_filters:
            qs = qs.filter(**safe_filters)

        # Limit to avoid heavy responses
        results = list(qs.values()[:50])
        return {'model': model_path, 'results': results}

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _get_model_class(self, model_path: str):
        try:
            app_label, model_name = model_path.split('.')
            return apps.get_model(app_label, model_name)
        except Exception:
            raise ValidationError({'detail': f'Invalid model path: {model_path}'})

    def _get_serializer_class(self, schema: Dict[str, Any]):
        serializer_path = schema.get('serializer')
        if not serializer_path:
            raise ValidationError({'detail': 'Serializer not found for model'})
        module_path, class_name = serializer_path.rsplit('.', 1)
        try:
            module = importlib.import_module(module_path)
            return getattr(module, class_name)
        except Exception as e:
            raise ValidationError({'detail': f'Cannot load serializer {serializer_path}: {e}'})

    def _map_fields(self, incoming: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """Map intent fields to real field names using schema synonyms and ignore unknowns."""
        mapped = {}
        fields_meta = schema.get('fields', {})
        for user_key, value in (incoming or {}).items():
            if user_key in fields_meta:
                mapped[user_key] = value
                continue
            # check synonyms
            for field_name, meta in fields_meta.items():
                if user_key.lower() in [s.lower() for s in meta.get('synonyms', [])]:
                    mapped[field_name] = value
                    break
        return mapped

    def _inject_org_if_needed(self, fields: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        if 'organization' in schema.get('fields', {}) and hasattr(self.user, 'organization') and self.user.organization:
            if fields.get('organization') and fields['organization'] != self.user.organization_id:
                raise ValidationError({'detail': 'Organization mismatch'})
            fields = dict(fields)
            fields['organization'] = self.user.organization_id
        return fields

    def _resolve_relationships(self, fields: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve FK and M2M fields using schema metadata."""
        resolved = dict(fields)
        fields_meta = schema.get('fields', {})
        for fname, meta in fields_meta.items():
            if fname not in resolved:
                continue
            value = resolved[fname]
            # ForeignKey
            if meta.get('related_model') and meta.get('type') == 'ForeignKey':
                resolved[fname] = self._resolve_fk(meta['related_model'], value)
            # ManyToMany
            if meta.get('related_model') and meta.get('type') == 'ManyToManyField':
                resolved[fname] = self._resolve_m2m(meta['related_model'], value)
        return resolved

    def _resolve_fk(self, related_model_path: str, value: Any):
        model_cls = self._get_model_class(related_model_path)
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            qs = model_cls.objects.all()
            # org scoping if present
            if hasattr(model_cls, 'organization_id') and getattr(self.user, 'organization_id', None):
                qs = qs.filter(organization_id=self.user.organization_id)
            # heuristics for user-like models
            if model_cls._meta.model_name in ['user', 'customuser']:
                for field in ['email', 'username']:
                    if field in [f.name for f in model_cls._meta.fields]:
                        found = qs.filter(**{field: value}).values_list('id', flat=True)[:1]
                        if found:
                            return found[0]
            for field in ['code', 'name', 'title']:
                if field in [f.name for f in model_cls._meta.fields]:
                    found = qs.filter(**{field: value}).values_list('id', flat=True)[:1]
                    if found:
                        return found[0]
        return value  # fallback unmodified

    def _resolve_m2m(self, related_model_path: str, value: Any):
        model_cls = self._get_model_class(related_model_path)
        if not isinstance(value, (list, tuple)):
            return value
        resolved_ids = []
        for item in value:
            if isinstance(item, int):
                resolved_ids.append(item)
                continue
            if isinstance(item, str):
                qs = model_cls.objects.all()
                if hasattr(model_cls, 'organization_id') and getattr(self.user, 'organization_id', None):
                    qs = qs.filter(organization_id=self.user.organization_id)
                if model_cls._meta.model_name in ['user', 'customuser']:
                    for field in ['email', 'username']:
                        if field in [f.name for f in model_cls._meta.fields]:
                            found = qs.filter(**{field: item}).values_list('id', flat=True)[:1]
                            if found:
                                resolved_ids.append(found[0])
                                break
                    continue
                for field in ['code', 'name', 'title']:
                    if field in [f.name for f in model_cls._meta.fields]:
                        found = qs.filter(**{field: item}).values_list('id', flat=True)[:1]
                        if found:
                            resolved_ids.append(found[0])
                            break
        return resolved_ids

    def _check_permissions(self, action: str, model_path: str):
        app_label, model_name = model_path.split('.')
        model_lower = model_name.lower()
        perm_map = {
            'create': f'{app_label}.add_{model_lower}',
            'update': f'{app_label}.change_{model_lower}',
            'delete': f'{app_label}.delete_{model_lower}',
            'read': f'{app_label}.view_{model_lower}',
        }
        perm = perm_map.get(action)
        if perm and not self.user.has_perm(perm):
            raise ValidationError({'detail': 'Permission denied'})

    def _audit(self, event_type: str, model_path: str, obj_id: Any, payload: Dict[str, Any]):
        try:
            from apps.users.models import SecurityAuditLog
            ip = self.request.META.get('REMOTE_ADDR', '') if self.request else ''
            ua = self.request.META.get('HTTP_USER_AGENT', '') if self.request else ''
            SecurityAuditLog.log_event(
                self.user,
                event_type,
                ip,
                ua,
                details={'model': model_path, 'id': obj_id, 'payload': payload},
            )
        except Exception:
            # Do not break main flow on audit errors
            pass

    def _strip_read_only(self, fields: Dict[str, Any], schema: Dict[str, Any]):
        """Remove read-only fields based on serializer info; return (filtered, warnings)."""
        warnings = []
        serializer_info = schema.get('serializer_info') or {}
        read_only = set(serializer_info.get('read_only_fields') or [])
        filtered = dict(fields)
        for ro in list(read_only):
            if ro in filtered:
                warnings.append(f"Field '{ro}' is read-only and will be ignored.")
                filtered.pop(ro, None)
        return filtered, warnings

    def _missing_required_fields(self, mapped: Dict[str, Any], schema: Dict[str, Any]):
        required_fields = [
            name for name, meta in (schema.get('fields') or {}).items()
            if meta.get('required')
        ]
        return [f for f in required_fields if f not in mapped]
