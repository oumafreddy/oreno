"""
Enhanced Schema Indexer for Oreno GRC
Comprehensively indexes all models, serializers, and forms with full metadata
"""
import inspect
from typing import Dict, Any, List, Optional, Set
from django.apps import apps
from django.db import models
from django.core.validators import BaseValidator
from django.forms import ModelForm
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
import logging

logger = logging.getLogger('services.agent.schema_index')


class EnhancedSchemaIndex:
    """
    Comprehensive schema indexer that understands:
    - Model fields (types, validators, choices, relationships)
    - Serializer fields (read_only, required, validators)
    - Form fields (widgets, help_text, labels)
    - Workflow states and transitions
    - Field dependencies and relationships
    """
    
    def __init__(self):
        self.models: Dict[str, Dict[str, Any]] = {}
        self.serializers: Dict[str, Any] = {}
        self.forms: Dict[str, Any] = {}
        self._serializer_cache: Dict[str, Any] = {}
        self._form_cache: Dict[str, Any] = {}
        
    def build(self, target_apps: Optional[Set[str]] = None) -> 'EnhancedSchemaIndex':
        """
        Build comprehensive schema index for all models
        
        Args:
            target_apps: Set of app names to index (None = all apps)
        """
        if target_apps is None:
            # Default to GRC apps
            target_apps = {
                "audit", "risk", "compliance", "contracts", 
                "legal", "document_management", "ai_governance",
                "organizations", "users"
            }
        
        logger.info(f"Building schema index for apps: {target_apps}")
        
        # Index all models
        for app_config in apps.get_app_configs():
            app_name = app_config.name.split('.')[-1]
            if app_name in target_apps:
                for model in app_config.get_models():
                    model_key = f"{model._meta.app_label}.{model.__name__}"
                    try:
                        self.models[model_key] = self._index_model(model)
                        logger.debug(f"Indexed model: {model_key}")
                    except Exception as e:
                        logger.error(f"Error indexing model {model_key}: {e}")
        
        # Index serializers
        self._index_serializers()
        
        # Index forms
        self._index_forms()
        
        logger.info(f"Schema index built: {len(self.models)} models, {len(self.serializers)} serializers, {len(self.forms)} forms")
        return self
    
    def _index_model(self, model) -> Dict[str, Any]:
        """Index a single model with comprehensive metadata"""
        meta = model._meta
        
        # Check for workflow/state machine
        workflow_info = self._extract_workflow_info(model)
        
        # Get all fields
        fields = {}
        for field in meta.get_fields():
            if hasattr(field, 'name'):
                fields[field.name] = self._extract_field_info(field, model)
        
        # Get reverse relationships
        reverse_relations = self._extract_reverse_relations(model)
        
        # Get dependencies
        dependencies = self._extract_dependencies(model)
        
        return {
            "model": model.__name__,
            "app": meta.app_label,
            "db_table": meta.db_table,
            "fields": fields,
            "relationships": reverse_relations,
            "dependencies": dependencies,
            "workflow": workflow_info,
            "meta": {
                "verbose_name": meta.verbose_name,
                "verbose_name_plural": meta.verbose_name_plural,
                "ordering": getattr(meta, 'ordering', []),
                "unique_together": getattr(meta, 'unique_together', []),
                "indexes": [str(idx) for idx in getattr(meta, 'indexes', [])],
            }
        }
    
    def _extract_field_info(self, field, model) -> Dict[str, Any]:
        """Extract comprehensive information about a field"""
        info = {
            "type": field.__class__.__name__,
            "internal_type": getattr(field, 'get_internal_type', lambda: None)(),
            "name": field.name,
        }
        
        # Basic attributes
        if hasattr(field, 'null'):
            info["null"] = field.null
        if hasattr(field, 'blank'):
            info["blank"] = field.blank
        if hasattr(field, 'default'):
            default = field.default
            if default != models.NOT_PROVIDED:
                if callable(default):
                    info["default"] = f"<callable: {default.__name__}>"
                else:
                    info["default"] = default
        if hasattr(field, 'help_text'):
            info["help_text"] = str(field.help_text) if field.help_text else None
        if hasattr(field, 'verbose_name'):
            info["verbose_name"] = str(field.verbose_name)
        
        # Field-specific attributes
        if isinstance(field, models.CharField):
            info["max_length"] = field.max_length
        elif isinstance(field, models.TextField):
            info["max_length"] = None  # Unlimited
        elif isinstance(field, (models.IntegerField, models.PositiveIntegerField, 
                               models.SmallIntegerField, models.PositiveSmallIntegerField)):
            if hasattr(field, 'validators'):
                info["validators"] = [str(v) for v in field.validators]
        elif isinstance(field, models.DecimalField):
            info["max_digits"] = field.max_digits
            info["decimal_places"] = field.decimal_places
        elif isinstance(field, models.DateField):
            info["auto_now"] = getattr(field, 'auto_now', False)
            info["auto_now_add"] = getattr(field, 'auto_now_add', False)
        elif isinstance(field, models.DateTimeField):
            info["auto_now"] = getattr(field, 'auto_now', False)
            info["auto_now_add"] = getattr(field, 'auto_now_add', False)
        
        # Choices
        if hasattr(field, 'choices') and field.choices:
            info["choices"] = self._extract_choices(field.choices)
            info["has_choices"] = True
        else:
            info["has_choices"] = False
        
        # Relationships
        if isinstance(field, models.ForeignKey):
            info["related_model"] = f"{field.related_model._meta.app_label}.{field.related_model.__name__}"
            info["related_name"] = getattr(field, 'related_name', None)
            if hasattr(field, 'on_delete'):
                info["on_delete"] = field.on_delete.__name__ if hasattr(field.on_delete, '__name__') else str(field.on_delete)
            info["required"] = not field.null
        elif isinstance(field, models.ManyToManyField):
            info["related_model"] = f"{field.related_model._meta.app_label}.{field.related_model.__name__}"
            info["related_name"] = getattr(field, 'related_name', None)
            if hasattr(field, 'through') and field.through:
                try:
                    info["through"] = field.through._meta.db_table
                except AttributeError:
                    info["through"] = None
            else:
                info["through"] = None
        elif isinstance(field, models.OneToOneField):
            info["related_model"] = f"{field.related_model._meta.app_label}.{field.related_model.__name__}"
            info["related_name"] = getattr(field, 'related_name', None)
            if hasattr(field, 'on_delete'):
                info["on_delete"] = field.on_delete.__name__ if hasattr(field.on_delete, '__name__') else str(field.on_delete)
        
        # Validators
        if hasattr(field, 'validators'):
            validators = []
            for validator in field.validators:
                if isinstance(validator, BaseValidator):
                    validators.append({
                        "type": validator.__class__.__name__,
                        "code": validator.code if hasattr(validator, 'code') else None,
                        "message": str(validator.message) if hasattr(validator, 'message') else None,
                    })
                else:
                    validators.append({
                        "type": validator.__name__ if hasattr(validator, '__name__') else str(validator),
                    })
            if validators:
                info["validators"] = validators
        
        # Check if field is required
        info["required"] = not (getattr(field, 'null', False) or getattr(field, 'blank', False))
        
        # Synonyms (common field name variations)
        info["synonyms"] = self._get_field_synonyms(field.name, info.get("type"))
        
        return info
    
    def _extract_choices(self, choices) -> List[Dict[str, Any]]:
        """Extract choices in a structured format"""
        result = []
        for choice in choices:
            if isinstance(choice, (list, tuple)) and len(choice) == 2:
                result.append({
                    "value": choice[0],
                    "label": str(choice[1]),
                    "display": str(choice[1])
                })
            else:
                result.append({
                    "value": choice,
                    "label": str(choice),
                    "display": str(choice)
                })
        return result
    
    def _extract_reverse_relations(self, model) -> Dict[str, Any]:
        """Extract reverse relationships (related_name)"""
        relations = {}
        for field in model._meta.get_fields():
            if hasattr(field, 'related_name') and field.related_name:
                if isinstance(field, models.ForeignKey):
                    relations[field.related_name] = {
                        "type": "reverse_fk",
                        "related_model": f"{field.related_model._meta.app_label}.{field.related_model.__name__}",
                        "field_name": field.name,
                    }
                elif isinstance(field, models.ManyToManyField):
                    relations[field.related_name] = {
                        "type": "reverse_m2m",
                        "related_model": f"{field.related_model._meta.app_label}.{field.related_model.__name__}",
                        "field_name": field.name,
                    }
        return relations
    
    def _extract_dependencies(self, model) -> Dict[str, List[str]]:
        """Extract model dependencies (required ForeignKeys, etc.)"""
        required = []
        optional = []
        
        for field in model._meta.get_fields():
            if isinstance(field, (models.ForeignKey, models.OneToOneField)):
                if not field.null:
                    required.append(field.name)
                else:
                    optional.append(field.name)
        
        return {
            "required": required,
            "optional": optional
        }
    
    def _extract_workflow_info(self, model) -> Dict[str, Any]:
        """Extract workflow/state machine information"""
        workflow_info = {
            "has_state_machine": False,
            "states": [],
            "transitions": {},
            "state_field": None
        }
        
        # Check for ApprovalStateMixin or similar
        if hasattr(model, 'STATE_CHOICES') or hasattr(model, 'STATUS_CHOICES'):
            # Find state field
            for field in model._meta.get_fields():
                if hasattr(field, 'choices') and field.choices:
                    # Check if this looks like a state field
                    field_name = field.name.lower()
                    if 'state' in field_name or 'status' in field_name:
                        workflow_info["has_state_machine"] = True
                        workflow_info["state_field"] = field.name
                        workflow_info["states"] = [choice[0] for choice in field.choices]
                        
                        # Try to detect transitions (simple heuristic)
                        # In a real implementation, you'd parse the state machine
                        if len(workflow_info["states"]) > 0:
                            # Default: can transition from any state to any state
                            # This should be enhanced with actual state machine logic
                            for state in workflow_info["states"]:
                                workflow_info["transitions"][state] = workflow_info["states"]
                        break
        
        return workflow_info
    
    def _get_field_synonyms(self, field_name: str, field_type: str) -> List[str]:
        """Get common synonyms for field names"""
        synonyms_map = {
            "name": ["title", "workplan_name", "engagement_name", "risk_name"],
            "title": ["name", "workplan_name", "engagement_name"],
            "fiscal_year": ["year", "fiscal", "fy"],
            "year": ["fiscal_year", "fiscal", "fy"],
            "state": ["status", "approval_status", "workflow_state"],
            "status": ["state", "approval_status", "workflow_state"],
            "code": ["identifier", "id_code", "reference"],
            "description": ["desc", "details", "summary"],
            "created_at": ["created", "date_created", "created_date"],
            "updated_at": ["updated", "modified", "last_modified"],
            "organization": ["org", "company", "tenant"],
        }
        return synonyms_map.get(field_name.lower(), [])
    
    def _index_serializers(self):
        """Index all serializers and map them to models"""
        # Import common serializer modules
        serializer_modules = [
            'audit.serializers',
            'risk.serializers',
            'compliance.serializers',
            'contracts.serializers',
            'legal.serializers',
        ]
        
        for module_name in serializer_modules:
            try:
                module = __import__(module_name, fromlist=[''])
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, ModelSerializer) and 
                        obj != ModelSerializer and
                        hasattr(obj, 'Meta') and
                        hasattr(obj.Meta, 'model')):
                        
                        model = obj.Meta.model
                        model_key = f"{model._meta.app_label}.{model.__name__}"
                        
                        # Extract serializer info
                        serializer_info = self._extract_serializer_info(obj, model)
                        self.serializers[model_key] = serializer_info
                        
                        # Link to model
                        if model_key in self.models:
                            self.models[model_key]["serializer"] = f"{module_name}.{name}"
                            self.models[model_key]["serializer_info"] = serializer_info
                        
            except ImportError as e:
                logger.debug(f"Could not import {module_name}: {e}")
            except Exception as e:
                # Log but don't fail - some serializers may have issues
                logger.warning(f"Error indexing serializers from {module_name}: {e}")
                continue  # Continue with other modules
    
    def _extract_serializer_info(self, serializer_class, model) -> Dict[str, Any]:
        """Extract information from a serializer"""
        try:
            meta = serializer_class.Meta
            fields_info = {}
            
            # Get all fields from serializer (handle errors gracefully)
            try:
                serializer_instance = serializer_class()
                for field_name, field in serializer_instance.fields.items():
                    try:
                        fields_info[field_name] = {
                            "read_only": field.read_only,
                            "required": field.required,
                            "allow_null": getattr(field, 'allow_null', False),
                            "allow_blank": getattr(field, 'allow_blank', False),
                            "type": field.__class__.__name__,
                        }
                        
                        # Extract validators
                        if hasattr(field, 'validators'):
                            validators = []
                            for validator in field.validators:
                                try:
                                    validators.append({
                                        "type": validator.__class__.__name__,
                                    })
                                except Exception:
                                    pass  # Skip invalid validators
                            if validators:
                                fields_info[field_name]["validators"] = validators
                    except Exception as e:
                        logger.debug(f"Error extracting field {field_name} from serializer: {e}")
                        continue  # Skip problematic fields
            except Exception as e:
                logger.warning(f"Error instantiating serializer {serializer_class.__name__}: {e}")
                # Return minimal info if we can't instantiate
                fields_info = {}
            
            return {
                "class": f"{serializer_class.__module__}.{serializer_class.__name__}",
                "fields": fields_info,
                "read_only_fields": getattr(meta, 'read_only_fields', []),
                "fields_list": getattr(meta, 'fields', '__all__'),
            }
        except Exception as e:
            logger.error(f"Error extracting serializer info for {serializer_class.__name__}: {e}")
            return {
                "class": f"{serializer_class.__module__}.{serializer_class.__name__}",
                "fields": {},
                "error": str(e)
            }
    
    def _index_forms(self):
        """Index all forms and map them to models"""
        form_modules = [
            'audit.forms',
            'risk.forms',
            'compliance.forms',
            'contracts.forms',
            'legal.forms',
        ]
        
        for module_name in form_modules:
            try:
                module = __import__(module_name, fromlist=[''])
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, ModelForm) and 
                        obj != ModelForm and
                        hasattr(obj, 'Meta') and
                        hasattr(obj.Meta, 'model')):
                        
                        model = obj.Meta.model
                        model_key = f"{model._meta.app_label}.{model.__name__}"
                        
                        # Extract form info
                        form_info = self._extract_form_info(obj, model)
                        self.forms[model_key] = form_info
                        
                        # Link to model
                        if model_key in self.models:
                            self.models[model_key]["form"] = f"{module_name}.{name}"
                            self.models[model_key]["form_info"] = form_info
                        
            except ImportError as e:
                logger.debug(f"Could not import {module_name}: {e}")
            except Exception as e:
                # Log but don't fail - some forms may have issues
                logger.warning(f"Error indexing forms from {module_name}: {e}")
                continue  # Continue with other modules
    
    def _extract_form_info(self, form_class, model) -> Dict[str, Any]:
        """Extract information from a form"""
        meta = form_class.Meta
        fields_info = {}
        
        # Get all fields from form
        form_instance = form_class()
        for field_name, field in form_instance.fields.items():
            fields_info[field_name] = {
                "required": field.required,
                "widget": field.widget.__class__.__name__,
                "help_text": str(field.help_text) if field.help_text else None,
                "label": str(field.label) if field.label else None,
            }
        
        return {
            "class": f"{form_class.__module__}.{form_class.__name__}",
            "fields": fields_info,
            "fields_list": getattr(meta, 'fields', '__all__'),
        }
    
    def get_model_schema(self, model_path: str) -> Optional[Dict[str, Any]]:
        """Get complete schema for a model"""
        return self.models.get(model_path)
    
    def get_field_info(self, model_path: str, field_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed info about a specific field"""
        model_schema = self.get_model_schema(model_path)
        if model_schema and field_name in model_schema.get("fields", {}):
            return model_schema["fields"][field_name]
        return None
    
    def list_models(self, app_name: Optional[str] = None) -> List[str]:
        """List all indexed models, optionally filtered by app"""
        if app_name:
            return [key for key in self.models.keys() if key.startswith(f"{app_name}.")]
        return list(self.models.keys())
    
    def get_serializer_for_model(self, model_path: str) -> Optional[Dict[str, Any]]:
        """Get serializer info for a model"""
        return self.serializers.get(model_path)
    
    def get_form_for_model(self, model_path: str) -> Optional[Dict[str, Any]]:
        """Get form info for a model"""
        return self.forms.get(model_path)


# Singleton instance
_schema_index: Optional[EnhancedSchemaIndex] = None


def get_schema_index() -> EnhancedSchemaIndex:
    """Get or create the global schema index instance"""
    global _schema_index
    if _schema_index is None:
        _schema_index = EnhancedSchemaIndex().build()
    return _schema_index


def rebuild_schema_index():
    """Rebuild the schema index (useful after migrations)"""
    global _schema_index
    _schema_index = EnhancedSchemaIndex().build()
    return _schema_index
