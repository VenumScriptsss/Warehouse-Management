from django.db import models
from django.contrib.auth.models import AbstractUser
# from inventory.models import WarehouseModel

class ReportModel(models.Model):
    """
    Model to store all user activities and system reports
    """
    ACTIVITY_CHOICES = [
        ('CREATE', 'Create'),
        ('EDIT', 'Edit'),
        ('DELETE', 'Delete'),
        ('VIEW', 'View'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('IMPORT', 'Import'),
        ('EXPORT', 'Export'),
        ('SYSTEM', 'System'),
        ('REPORT', 'Report'),
    ]

    # User who performed the activity
    user = models.ForeignKey('UserModel', on_delete=models.SET_NULL, null=True, blank=True)

    # Type of activity performed
    activity = models.CharField(max_length=20, choices=ACTIVITY_CHOICES)

    # ID of the object that was affected (if applicable)
    object_id = models.PositiveIntegerField(null=True, blank=True)

    # Name of the model/class that was affected
    object_model = models.CharField(max_length=100, null=True, blank=True)

    # When the activity was performed
    performed_at = models.DateTimeField(auto_now_add=True)

    # IP address of the user who performed the activity
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    # User agent/browser information
    user_agent = models.TextField(null=True, blank=True)

    # Additional details about the activity
    details = models.JSONField(null=True, blank=True)

    # Any changes made (for edit operations)
    changes = models.JSONField(null=True, blank=True)

    # Status of the activity (success/failure)
    status = models.CharField(max_length=20, default='SUCCESS', choices=[
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('PENDING', 'Pending'),
    ])

    class Meta:
        verbose_name = 'Activity Report'
        verbose_name_plural = 'Activity Reports'
        ordering = ['-performed_at']
        indexes = [
            models.Index(fields=['-performed_at']),
            models.Index(fields=['user']),
            models.Index(fields=['activity']),
            models.Index(fields=['object_model']),
        ]

    def __str__(self):
        user_name = self.user.username if self.user else 'System'
        return f"{user_name} - {self.activity} - {self.performed_at}"

    def get_activity_display(self):
        """Get the human-readable activity name"""
        return dict(self.ACTIVITY_CHOICES).get(self.activity, self.activity)

class UserModel(AbstractUser):
    ROLE_CHOICES = (
        ("admin", "Admin"),
        ("operator", "Operator"),
        ("manager", "Manager"),
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="operator"
    )
    warehouse = models.ForeignKey('inventory.WarehouseModel', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.username} ({self.role})"

    def save(self, *args, **kwargs):
        # Automatically set role to admin for superusers
        if self.is_superuser:
            self.role = 'admin'
        super().save(*args, **kwargs)
