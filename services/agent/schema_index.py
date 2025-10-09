from django.apps import apps

class SchemaIndex:
    def __init__(self):
        self.models = {}

    def build(self):
        target = {"audit","risk","compliance"}
        for app_config in apps.get_app_configs():
            if app_config.name.split('.')[-1] in target:
                for model in app_config.get_models():
                    key = f"{model._meta.app_label}.{model.__name__}"
                    self.models[key] = self._model_fields(model)
        return self

    def _model_fields(self, model):
        fields = {}
        for f in model._meta.get_fields():
            if hasattr(f, 'attname'):
                fields[f.name] = {
                    'type': f.get_internal_type(),
                    'null': getattr(f, 'null', False),
                    'choices': getattr(f, 'choices', None),
                    'related': getattr(f, 'related_model', None) and str(f.related_model),
                }
        return fields
