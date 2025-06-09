// audit_workflow.js
document.addEventListener('DOMContentLoaded', function() {
  const workflowSteps = document.querySelectorAll('.workflow-step');
  workflowSteps.forEach(step => {
    step.addEventListener('mouseenter', function() {
      this.classList.add('shadow-lg');
    });
    step.addEventListener('mouseleave', function() {
      this.classList.remove('shadow-lg');
    });
  });
}); 