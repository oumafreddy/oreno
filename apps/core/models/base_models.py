from django.db import models
from django.utils.translation import gettext_lazy as _

class BaseModel(models.Model):
    """
    Base model class providing common functionality for all models.
    """
    class Meta:
        abstract = True
        verbose_name = _('Base Model')
        verbose_name_plural = _('Base Models') 