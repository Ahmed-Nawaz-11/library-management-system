from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('librarian', 'Librarian'),
        ('member', 'Member'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    phone = models.CharField(max_length=15, blank=True)
    membership_expiry = models.DateField(null=True, blank=True)
    is_suspended = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.username} ({self.role})"