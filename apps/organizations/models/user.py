# apps/organizations/models/user.py
from django.db import models
from users.models import CustomUser

class OrganizationUser(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('staff', 'Staff'),
    ]

    user = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.CASCADE,
        related_name='organization_memberships'
    )
    organization = models.ForeignKey(
        'Organization',
        on_delete=models.CASCADE,
        related_name='members'
    )
    role = models.CharField(
        max_length=50,
        choices=ROLE_CHOICES,
        default='staff'
    )

    class Meta:
        unique_together = ('user', 'organization')

    def __str__(self):
        return f"{self.user.email} in {self.organization}"