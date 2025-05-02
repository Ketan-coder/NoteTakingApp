import uuid

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
# from ckeditor.fields import RichTextField
from django.dispatch import receiver


# Create your models here.
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    firstName = models.CharField(max_length=150)
    lastName = models.CharField(max_length=150)
    email = models.EmailField(max_length=150)
    # image = models.ImageField(default='OIP.jfif',upload_to='profile_pics')
    bio = models.TextField(default="Hello, I am using Timely")
    email_confirmation_token = models.UUIDField(unique=True, blank=True, null=True)
    extra_fields = models.JSONField(
        blank=True, null=True, default=dict, 
    )  # For any extra fields you want to add

    def save(self, *args, **kwargs):
        if not self.email_confirmation_token:
            self.email_confirmation_token = uuid.uuid4()  # Generate only if empty
        self.extra_fields['last_logged_in'] = str(self.user.last_login)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username}'s Profile"


class ThemeState(models.TextChoices):
    OFF = "off", "Off"
    SYSTEM = "auto", "Auto"
    LIGHT = "light", "Light"
    DARK = "dark", "Dark"

class TextSize(models.IntegerChoices):
    SMALL = 0, "Small"
    MEDIUM = 1, "Medium"
    LARGE = 2, "Large"
    EXTRA_LARGE = 3, "Extra Large"

class UserPreferences(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, unique=True)
    theme = models.CharField(max_length=10, choices=ThemeState.choices, default=ThemeState.SYSTEM)
    text_size = models.PositiveSmallIntegerField(choices=TextSize.choices, default=TextSize.MEDIUM)
    biometric_enabled = models.BooleanField(default=True)
    notifications_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    extra_settings = models.JSONField(
        blank=True, null=True, default=dict,
    )  # For any extra settings you want to add
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.profile.user.username}'s Settings"