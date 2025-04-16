# apps/core/mixins/state.py
from django_fsm import FSMField, transition
from django.db import models

class ApprovalStateMixin(models.Model):
    STATE_DRAFT = 'draft'
    STATE_PENDING = 'pending_approval'
    STATE_APPROVED = 'approved'
    STATE_REJECTED = 'rejected'
    STATE_CHOICES = (
        (STATE_DRAFT, 'Draft'),
        (STATE_PENDING, 'Pending Approval'),
        (STATE_APPROVED, 'Approved'),
        (STATE_REJECTED, 'Rejected'),
    )

    state = FSMField(default=STATE_DRAFT, protected=True)

    @transition(field=state, source=STATE_DRAFT, target=STATE_PENDING)
    def submit_for_approval(self):
        pass

    @transition(field=state, source=STATE_PENDING, target=STATE_APPROVED)
    def approve(self):
        pass

    @transition(field=state, source=STATE_PENDING, target=STATE_REJECTED)
    def reject(self):
        pass

    class Meta:
        abstract = True