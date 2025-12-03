"""
Context-Aware Form Agent with Guardrails
Intelligently pre-fills form fields across all apps using schema intelligence
"""
from typing import Dict, Any, Optional, List, Tuple
from django.apps import apps
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import models
import logging
import re

from .schema_index import get_schema_index
from organizations.models import Organization  # type: ignore[reportMissingImports]

logger = logging.getLogger('services.agent.form_agent')


class FormAgent:
    """
    Context-aware agent that intelligently pre-fills form fields across all apps.
    
    Features:
    - Understands all models via schema index
    - Maps user input to form fields (synonym matching)
    - Applies smart defaults based on context
    - Resolves relationships (ForeignKey, ManyToMany)
    - Security guardrails (permissions, validation)
    - Works across all apps dynamically
    """
    
    def __init__(self, user, organization: Optional[Organization] = None):
        """
        Initialize form agent with user and organization context
        
        Args:
            user: Django user object
            organization: Organization object (auto-detected from user if not provided)
        """
        self.user = user
        self.organization = organization or getattr(user, 'organization', None)
        self.schema_index = get_schema_index()
        
        if not self.organization:
            logger.warning(f"FormAgent initialized without organization for user {user.id}")
    
    def prefill_form(self, model_path: str, user_input: Dict[str, Any], 
                    context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Pre-fill form fields for a model based on user input and context
        
        Args:
            model_path: Model path (e.g., 'audit.AuditWorkplan')
            user_input: User-provided field values (may use synonyms)
            context: Additional context (e.g., related objects, current page)
        
        Returns:
            Dict with:
            - 'fields': Mapped and pre-filled field values
            - 'suggestions': Suggested values for missing fields
            - 'warnings': Any warnings about the input
            - 'security_checks': Security validation results
        """
        # Get model schema
        schema = self.schema_index.get_model_schema(model_path)
        if not schema:
            raise ValueError(f"Model '{model_path}' not found in schema index")
        
        # Map user input to actual field names (handle synonyms)
        mapped_fields = self._map_input_to_fields(user_input, schema)
        
        # Apply smart defaults for missing required fields
        smart_defaults = self._generate_smart_defaults(model_path, schema, mapped_fields, context)
        mapped_fields.update(smart_defaults)
        
        # Resolve relationships (ForeignKey, ManyToMany)
        resolved_fields = self._resolve_relationships(model_path, schema, mapped_fields, context)
        
        # Security guardrails
        security_checks = self._check_security(model_path, schema, resolved_fields)
        
        # Generate suggestions for optional fields
        suggestions = self._generate_suggestions(model_path, schema, resolved_fields, context)
        
        # Validate field values
        validation = self._validate_fields(model_path, schema, resolved_fields)
        
        return {
            'fields': resolved_fields,
            'suggestions': suggestions,
            'warnings': validation.get('warnings', []),
            'errors': validation.get('errors', []),
            'security_checks': security_checks,
            'missing_required': validation.get('missing_required', []),
            'ready_to_save': len(validation.get('errors', [])) == 0 and len(validation.get('missing_required', [])) == 0
        }
    
    def _map_input_to_fields(self, user_input: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """Map user input to actual field names using synonyms"""
        mapped = {}
        fields = schema.get('fields', {})
        
        for input_key, input_value in user_input.items():
            # Try exact match first
            if input_key in fields:
                mapped[input_key] = input_value
                continue
            
            # Try synonym matching
            found = False
            for field_name, field_info in fields.items():
                synonyms = field_info.get('synonyms', [])
                if input_key.lower() in [s.lower() for s in synonyms] or input_key.lower() == field_name.lower():
                    mapped[field_name] = input_value
                    found = True
                    logger.debug(f"Mapped '{input_key}' -> '{field_name}' (synonym)")
                    break
            
            if not found:
                logger.debug(f"Could not map input field '{input_key}' to any model field")
        
        return mapped
    
    def _generate_smart_defaults(self, model_path: str, schema: Dict[str, Any], 
                                 mapped_fields: Dict[str, Any], context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate smart defaults for missing required fields"""
        defaults = {}
        fields = schema.get('fields', {})
        
        for field_name, field_info in fields.items():
            # Skip if already provided
            if field_name in mapped_fields:
                continue
            
            # Only generate defaults for required fields
            if not field_info.get('required', False):
                continue
            
            # Auto-inject organization
            if field_name == 'organization' and self.organization:
                defaults['organization'] = self.organization.id
                continue
            
            # Auto-inject created_by/updated_by
            if field_name in ['created_by', 'updated_by', 'owner', 'assigned_to']:
                defaults[field_name] = self.user.id
                continue
            
            # Set default state (first state in workflow)
            if field_name == schema.get('workflow', {}).get('state_field'):
                workflow = schema.get('workflow', {})
                if workflow.get('has_state_machine') and workflow.get('states'):
                    defaults[field_name] = workflow['states'][0]  # First state (usually 'draft')
                continue
            
            # Date fields
            if field_info.get('type') == 'DateField':
                if field_info.get('auto_now_add'):
                    defaults[field_name] = timezone.now().date().isoformat()
                elif 'date_identified' in field_name or 'created_date' in field_name:
                    defaults[field_name] = timezone.now().date().isoformat()
            
            # DateTime fields
            elif field_info.get('type') == 'DateTimeField':
                if field_info.get('auto_now_add'):
                    defaults[field_name] = timezone.now().isoformat()
            
            # Auto-generate codes
            if 'code' in field_name.lower() and field_info.get('type') == 'CharField':
                code = self._generate_code(model_path, field_name, context)
                if code:
                    defaults[field_name] = code
            
            # Use model default if available
            if 'default' in field_info:
                default_value = field_info['default']
                if not isinstance(default_value, str) or not default_value.startswith('<callable:'):
                    defaults[field_name] = default_value
        
        return defaults
    
    def _generate_code(self, model_path: str, field_name: str, context: Optional[Dict[str, Any]]) -> Optional[str]:
        """Generate a unique code for a field"""
        try:
            model = apps.get_model(*model_path.split('.'))
            
            # Try to get context for code generation
            fiscal_year = context.get('fiscal_year') if context else None
            if not fiscal_year:
                fiscal_year = timezone.now().year
            
            # Generate code pattern: YYYY-XXX
            prefix = str(fiscal_year)
            
            # Find existing codes with same prefix
            existing_codes = model.objects.filter(
                **{f"{field_name}__startswith": prefix}
            ).values_list(field_name, flat=True)
            
            # Find next available number
            max_num = 0
            for code in existing_codes:
                try:
                    num_part = code.split('-')[-1] if '-' in code else code[-3:]
                    num = int(num_part)
                    max_num = max(max_num, num)
                except (ValueError, IndexError):
                    pass
            
            next_num = max_num + 1
            return f"{prefix}-{next_num:03d}"
        
        except Exception as e:
            logger.debug(f"Could not generate code for {model_path}.{field_name}: {e}")
            return None
    
    def _resolve_relationships(self, model_path: str, schema: Dict[str, Any], 
                              mapped_fields: Dict[str, Any], context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Resolve ForeignKey and ManyToMany relationships"""
        resolved = mapped_fields.copy()
        fields = schema.get('fields', {})
        
        for field_name, field_value in mapped_fields.items():
            if field_name not in fields:
                continue
            
            field_info = fields[field_name]
            field_type = field_info.get('type')
            
            # Resolve ForeignKey by name/code
            if field_type == 'ForeignKey' and field_value:
                resolved_value = self._resolve_foreign_key(
                    field_info.get('related_model'),
                    field_value,
                    field_name
                )
                if resolved_value:
                    resolved[field_name] = resolved_value
                else:
                    logger.warning(f"Could not resolve ForeignKey {field_name} with value {field_value}")
            
            # Resolve ManyToMany (list of names/codes)
            elif field_type == 'ManyToManyField' and isinstance(field_value, list):
                resolved_list = []
                for item in field_value:
                    resolved_item = self._resolve_foreign_key(
                        field_info.get('related_model'),
                        item,
                        field_name
                    )
                    if resolved_item:
                        resolved_list.append(resolved_item)
                if resolved_list:
                    resolved[field_name] = resolved_list
        
        return resolved
    
    def _resolve_foreign_key(self, related_model_path: Optional[str], value: Any, field_name: str) -> Optional[int]:
        """Resolve a ForeignKey value (name/code) to an ID"""
        if not related_model_path:
            return None
        
        try:
            model = apps.get_model(*related_model_path.split('.'))
            
            # If already an ID, return it
            if isinstance(value, int):
                return value
            
            # Try to find by name/title/code
            value_str = str(value).strip()
            
            # Common field names to search
            search_fields = ['name', 'title', 'code', 'email', 'username']
            
            for search_field in search_fields:
                if hasattr(model, search_field):
                    try:
                        obj = model.objects.filter(**{search_field: value_str}).first()
                        if obj:
                            # Check organization if model has it
                            if hasattr(obj, 'organization') and self.organization:
                                if obj.organization_id == self.organization.id:
                                    return obj.id
                            else:
                                return obj.id
                    except Exception:
                        continue
            
            # Try exact ID match
            try:
                obj_id = int(value_str)
                obj = model.objects.filter(id=obj_id).first()
                if obj:
                    # Check organization if model has it
                    if hasattr(obj, 'organization') and self.organization:
                        if obj.organization_id == self.organization.id:
                            return obj.id
                    else:
                        return obj.id
            except ValueError:
                pass
        
        except Exception as e:
            logger.debug(f"Error resolving ForeignKey {related_model_path} with value {value}: {e}")
        
        return None
    
    def _check_security(self, model_path: str, schema: Dict[str, Any], 
                       fields: Dict[str, Any]) -> Dict[str, Any]:
        """Security guardrails: permissions, validation, data isolation"""
        checks = {
            'passed': True,
            'warnings': [],
            'errors': []
        }
        
        # Check organization isolation
        if 'organization' in fields and self.organization:
            if fields['organization'] != self.organization.id:
                checks['errors'].append("Cannot set organization to different organization")
                checks['passed'] = False
            else:
                # Ensure organization is set
                fields['organization'] = self.organization.id
        
        # Check user permissions (basic check)
        # In production, you'd check actual Django permissions
        if not self.user.is_authenticated:
            checks['errors'].append("User must be authenticated")
            checks['passed'] = False
        
        # Check for read-only fields
        serializer_info = self.schema_index.get_serializer_for_model(model_path)
        if serializer_info:
            read_only_fields = serializer_info.get('read_only_fields', [])
            for field_name in read_only_fields:
                if field_name in fields:
                    checks['warnings'].append(f"Field '{field_name}' is read-only and will be ignored")
                    fields.pop(field_name, None)
        
        # Validate field types
        schema_fields = schema.get('fields', {})
        for field_name, field_value in list(fields.items()):
            if field_name not in schema_fields:
                checks['warnings'].append(f"Unknown field '{field_name}' will be ignored")
                fields.pop(field_name, None)
                continue
            
            field_info = schema_fields[field_name]
            
            # Type validation
            if field_info.get('type') == 'CharField':
                max_length = field_info.get('max_length')
                if max_length and len(str(field_value)) > max_length:
                    checks['errors'].append(f"Field '{field_name}' exceeds max length of {max_length}")
                    checks['passed'] = False
            
            # Choice validation
            if field_info.get('has_choices'):
                valid_choices = [c['value'] for c in field_info.get('choices', [])]
                if field_value not in valid_choices:
                    checks['errors'].append(f"Field '{field_name}' has invalid value. Valid choices: {valid_choices}")
                    checks['passed'] = False
        
        return checks
    
    def _validate_fields(self, model_path: str, schema: Dict[str, Any], 
                        fields: Dict[str, Any]) -> Dict[str, Any]:
        """Validate field values against schema"""
        validation = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'missing_required': []
        }
        
        schema_fields = schema.get('fields', {})
        
        # Check required fields
        for field_name, field_info in schema_fields.items():
            if field_info.get('required', False) and field_name not in fields:
                validation['missing_required'].append(field_name)
                validation['valid'] = False
        
        # Validate field values
        for field_name, field_value in fields.items():
            if field_name not in schema_fields:
                continue
            
            field_info = schema_fields[field_name]
            
            # Null check
            if field_value is None and not field_info.get('null', False):
                validation['errors'].append(f"Field '{field_name}' cannot be null")
                validation['valid'] = False
        
        return validation
    
    def _generate_suggestions(self, model_path: str, schema: Dict[str, Any], 
                             fields: Dict[str, Any], context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate suggestions for optional fields"""
        suggestions = {}
        schema_fields = schema.get('fields', {})
        
        # Suggest related objects based on context
        for field_name, field_info in schema_fields.items():
            if field_name in fields:  # Skip if already filled
                continue
            
            if field_info.get('type') == 'ForeignKey':
                related_model = field_info.get('related_model')
                if related_model:
                    # Suggest recent or related objects
                    suggested = self._suggest_related_objects(related_model, field_name, context)
                    if suggested:
                        suggestions[field_name] = suggested
        
        return suggestions
    
    def _suggest_related_objects(self, related_model_path: str, field_name: str, 
                                 context: Optional[Dict[str, Any]]) -> Optional[List[Dict[str, Any]]]:
        """Suggest related objects for a ForeignKey field"""
        try:
            model = apps.get_model(*related_model_path.split('.'))
            
            # Build queryset
            queryset = model.objects.all()
            
            # Filter by organization if applicable
            if hasattr(model, 'organization') and self.organization:
                queryset = queryset.filter(organization=self.organization)
            
            # Limit to recent items
            suggestions = []
            for obj in queryset.order_by('-created_at')[:5]:
                suggestions.append({
                    'id': obj.id,
                    'name': getattr(obj, 'name', getattr(obj, 'title', str(obj))),
                    'code': getattr(obj, 'code', None)
                })
            
            return suggestions if suggestions else None
        
        except Exception as e:
            logger.debug(f"Error suggesting related objects for {related_model_path}: {e}")
            return None

