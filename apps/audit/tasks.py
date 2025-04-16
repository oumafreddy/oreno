# audits/tasks.py
@app.task
def process_approval_chain(approval_id):
    approval = Approval.objects.get(id=approval_id)
    workflow = ApprovalWorkflow(approval.content_object)
    
    if approval.status == Approval.APPROVED:
        if hasattr(approval.content_object, 'next_approval_step'):
            next_step = approval.content_object.next_approval_step()
            if next_step:
                workflow.initiate_approval(next_step.approver)