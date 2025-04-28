# apps/core/mixins/state.py

from django.db import models
from django_fsm import FSMField, transition
from common.constants import DRAFT, PENDING, APPROVED, REJECTED, STATUS_CHOICES

class ApprovalStateMixin(models.Model):
    """
    Adds a `state` FSMField with transitions:
      draft → pending → approved or rejected.
    """
    state = FSMField(
        default=DRAFT,
        choices=STATUS_CHOICES,
        protected=True,
        verbose_name="Approval State",
        help_text="Current approval state.",
    )

    @transition(field=state, source=DRAFT,  target=PENDING)
    def submit_for_approval(self):
        pass

    @transition(field=state, source=PENDING, target=APPROVED)
    def approve(self):
        pass

    @transition(field=state, source=PENDING, target=REJECTED)
    def reject(self):
        pass

    class Meta:
        abstract = True
