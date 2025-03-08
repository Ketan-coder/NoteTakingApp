from django.db import models
from django.contrib.auth.models import User
# from ckeditor.fields import RichTextField
from django.dispatch import receiver
from django.db.models.signals import post_save
import uuid
# Create your models here.
class Profile(models.Model):
    user =models.OneToOneField(User, on_delete=models.CASCADE)
    firstName = models.CharField(max_length=150)
    lastName = models.CharField(max_length=150)
    email = models.EmailField(max_length=150)
    # image = models.ImageField(default='OIP.jfif',upload_to='profile_pics')
    bio = models.TextField(default="Hello, I am using Timely")
    email_confirmation_token = models.UUIDField(unique=True, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.email_confirmation_token:
            self.email_confirmation_token = uuid.uuid4()  # Generate only if empty
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username}'s Profile"
