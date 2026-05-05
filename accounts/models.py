from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings


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


class UserRefreshToken(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='refresh_tokens'
    )
    token = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_revoked = models.BooleanField(default=False)

    def is_valid(self):
        from django.utils import timezone
        return not self.is_revoked and self.expires_at > timezone.now()

    def __str__(self):
        return f"RefreshToken({self.user.username}, revoked={self.is_revoked})"