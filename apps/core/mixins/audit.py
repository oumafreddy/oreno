# apps/core/mixins/audit.py

from django.db import models, ProgrammingError
from django.conf import settings
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.utils.functional import cached_property

class AuditMixin(models.Model):
    """
    A mixin that adds audit trail functionality to a model.
    If the audit log table isn't present (e.g. on public schema), it skips quietly.
    """
    created_at = models.DateTimeField(auto_now_add=True, help_text='When created')
    updated_at = models.DateTimeField(auto_now=True,    help_text='When last updated')
    audit_logs = GenericRelation(
        'core.AuditLog',
        object_id_field='object_id',
        content_type_field='content_type'
    )

    class Meta:
        abstract = True

    @cached_property
    def _audit_log_model(self):
        from core.models import AuditLog
        return AuditLog

    def save(self, *args, **kwargs):
        # Always update timestamps
        if not self.id:
            self.created_at = timezone.now()
        self.updated_at = timezone.now()

        # Create audit log entry unless explicitly disabled
        create_log = kwargs.pop('create_audit_log', True)
        if create_log:
            user   = kwargs.pop('user', None)
            action = 'create' if not self.id else 'update'
            try:
                self.create_audit_log(user, action)
            except ProgrammingError:
                # Table missing (e.g. core_auditlog not migrated); skip logging
                from django.db import connection
                connection.rollback()

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if kwargs.pop('create_audit_log', True):
            try:
                self.create_audit_log(kwargs.pop('user', None), 'delete')
            except ProgrammingError:
                from django.db import connection
                connection.rollback()

        super().delete(*args, **kwargs)

    def create_audit_log(self, user, action):
        """
        Create an audit log entry for this model instance.
        May raise ProgrammingError if table not present.
        """
        content_type = ContentType.objects.get_for_model(self)
        changes = {}
        if action == 'update' and self.id:
            original = self.__class__.objects.get(id=self.id)
            for field in self._meta.fields:
                o = getattr(original, field.name)
                n = getattr(self,       field.name)
                if o != n:
                    changes[field.name] = {'old': str(o), 'new': str(n)}

        self._audit_log_model.objects.create(
            content_type=   content_type,
            object_id=      self.id or 0,
            user=           user,
            action=         action,
            changes=        changes,
            object_repr=    str(self),
            # you can add other fields here if desired...
        )

    @property
    def has_audit_access(self):
        return hasattr(self, 'organization') and self.organization.has_audit_enabled
