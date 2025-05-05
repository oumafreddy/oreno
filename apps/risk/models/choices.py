from common.constants import RISK_CATEGORY_CHOICES

RISK_RESPONSE_CHOICES = [
    ('mitigate', 'Mitigate/Reduce'),
    ('accept', 'Accept'),
    ('transfer', 'Transfer/Share'),
    ('avoid', 'Avoid/Terminate'),
    ('exploit', 'Exploit/Enhance'),
]

CONTROL_STATUS_CHOICES = [
    ('implemented', 'Implemented'),
    ('in-progress', 'In Progress'),
    ('not-implemented', 'Not Implemented'),
    ('planned', 'Planned'),
]

CONTROL_RATING_CHOICES = [
    ('effective', 'Effective'),
    ('partially-effective', 'Partially Effective'),
    ('ineffective', 'Ineffective'),
    ('not-assessed', 'Not Assessed'),
]

ACTION_PLAN_STATUS_CHOICES = [
    ('not-started', 'Not Started'),
    ('in-progress', 'In Progress'),
    ('completed', 'Completed'),
    ('overdue', 'Overdue'),
    ('cancelled', 'Cancelled'),
]

STATUS_CHOICES = [
    ('open', 'Open'),
    ('in-progress', 'In Progress'),
    ('closed', 'Closed'),
    ('archived', 'Archived'),
] 