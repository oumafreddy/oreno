# audits/services/workflow.py
class ApprovalWorkflow:
    def __init__(self, content_object):
        self.content_object = content_object
        self.approval_model = content_object.approval if hasattr(content_object, 'approval') else None

    def initiate_approval(self, requester):
        if self.content_object.state != self.content_object.STATE_DRAFT:
            raise InvalidStateError("Approval can only be initiated from draft state")

        approvers = self.content_object.get_approvers()
        if not approvers.exists():
            raise NoApproversError("No valid approvers configured")

        approval = Approval.objects.create(
            content_object=self.content_object,
            organization=self.content_object.organization,
            requester=requester,
            approver=approvers.first(),
            status=Approval.PENDING
        )
        
        self.content_object.submit_for_approval()
        self.content_object.save()
        
        NotificationService.notify_approver(approval)
        AuditLogger.log_approval_initiation(approval)
        
        return approval

    def process_approval(self, approver, decision, comments=''):
        if self.approval_model.status != Approval.PENDING:
            raise InvalidApprovalStateError("Approval is not in pending state")

        if decision == Approval.APPROVED:
            self.content_object.approve()
            next_step = self._handle_approval_chain()
        else:
            self.content_object.reject()
            next_step = self._handle_rejection()

        self.approval_model.status = decision
        self.approval_model.comments = comments
        self.approval_model.save()

        NotificationService.notify_requester(self.approval_model)
        AuditLogger.log_approval_decision(self.approval_model)

        return next_step