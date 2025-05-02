import datetime

from ckeditor.fields import RichTextField
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from django.db import models
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone
from Users.models import Profile
import uuid
from datetime import timezone as dt_timezone

# PRIORITY_LIST = [
#     ('Important','Important'),
#     ('Not Important','Not Important'),
# ]
# Create your models here.
class Notebook(models.Model):
    notebook_uuid:uuid = models.UUIDField(unique=True, blank=True, null=True)
    title: str = models.CharField(max_length=100)
    body: str = models.TextField()
    priority = models.IntegerField(default=0)
    # priority = models.CharField(choices=PRIORITY_LIST,default="Important",max_length=50)
    is_favourite = models.BooleanField(default=False)
    is_shared = models.BooleanField(default=False)
    is_public = models.BooleanField(default=False)
    shared_with = models.ManyToManyField(
        Profile, related_name="shared_notebooks", blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_password_protected: bool = models.BooleanField(default=False)
    is_password_entered: bool = models.BooleanField(default=False)
    is_accessed_recently: bool = models.BooleanField(default=False)
    password = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Enter the password to access this page",
    )
    author = models.ForeignKey(Profile, on_delete=models.CASCADE)
    extra_fields = models.JSONField(
        blank=True, null=True, default=dict, 
    )  # For any extra fields you want to add

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        if self.is_password_protected and not self.password:
            raise ValueError("Password is required for password-protected notebooks.")
        elif self.is_password_protected and self.password:
            if not self.password.startswith("pbkdf2_sha256$"):  # Avoid double hashing
                self.password = make_password(self.password)
        if not self.notebook_uuid:
            self.notebook_uuid = uuid.uuid4()
        super().save(*args, **kwargs)

    def check_password(self, password):
        check_password(password, self.password)

    # def check_password(self, password) -> bool:
    #     if self.password == password:
    #         return True
    #     else:
    #         return False


class SharedNotebook(models.Model):
    sharednotebook_uuid:uuid = models.UUIDField(unique=True, blank=True, null=True)
    notebook = models.OneToOneField(Notebook, on_delete=models.CASCADE)
    owner = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="notebook_owner"
    )
    # sharedTo = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='shared_to', blank=True, null=True)
    sharedTo = models.ManyToManyField(Profile, related_name="shared_to", blank=True)
    shared_at = models.DateTimeField(auto_now_add=True)
    shareable_link = models.URLField(blank=True, null=True)
    can_edit = models.BooleanField(default=False)
    extra_fields = models.JSONField(
        blank=True, null=True, default=dict, 
    )  # For any extra fields you want to add

    def save(self, request=None, *args, **kwargs):
        if not self.shared_at:
            self.shared_at = timezone.now() + timezone.timedelta(hours=5, minutes=30)

        # if not self.shareable_link:
        #     self.shareable_link = f'sharedNotebooks/'

        # if request:
        #     messages.success(request, f'Notebook shared successfully! Here is the link to view it: {self.shareable_link}')

        notebook = self.notebook
        notebook.is_shared = True
        notebook.save()
        if not self.sharednotebook_uuid:
            self.sharednotebook_uuid = uuid.uuid4()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        owner_name = (
            self.notebook.author.firstName if self.notebook.author else self.username
        )
        # shared_to_name = self.sharedTo.firstName if self.sharedTo.email else "Unknown"
        return f"{owner_name} shared this - {self.notebook.title}'s Notebook =>  Unkown"


class Page(models.Model):
    page_uuid:uuid = models.UUIDField(unique=True, blank=True, null=True)
    notebook = models.ForeignKey(Notebook, on_delete=models.CASCADE)
    title: str = models.CharField(max_length=100)
    body: str = models.TextField()
    # is_favourite = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(Profile, on_delete=models.CASCADE)
    extra_fields = models.JSONField(
        blank=True, null=True, default=dict, 
    )  # For any extra fields you want to add

    def __str__(self) -> str:
        return self.notebook.title + " " + self.title

    class Meta:
        ordering = ["order"]

    def save(self, *args, **kwargs):
        if self.order is None:  # Only assign order if not provided
            last_page = self.notebook.pages.order_by("-order").first()
            self.order = (
                (last_page.order + 1) if last_page else 1
            )  # Get next order for this notebook
        if not self.page_uuid:
            self.page_uuid = uuid.uuid4()
        super().save(*args, **kwargs)

    # def save(self, *args, **kwargs):
    #     if not self.updated_at:
    #         self.updated_at = timezone.now() + timezone.timedelta(hours=5, minutes=30)
    #     super().save(*args, **kwargs)


class SubPage(models.Model):
    subpage_uuid:uuid = models.UUIDField(unique=True, blank=True, null=True)
    notebook = models.ForeignKey(Notebook, on_delete=models.CASCADE)
    page = models.ForeignKey(Page, on_delete=models.CASCADE)
    title: str = models.CharField(max_length=100)
    body: str = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(Profile, on_delete=models.CASCADE)
    extra_fields = models.JSONField(
        blank=True, null=True, default=dict, 
    )  # For any extra fields you want to add

    def __str__(self) -> str:
        return self.page.title + " " + self.title

    def save(self, *args, **kwargs):
        if not self.subpage_uuid:
            self.subpage_uuid = uuid.uuid4()
    #     if not self.updated_at:
    #         self.updated_at = timezone.now() + timezone.timedelta(hours=5, minutes=30)
        super().save(*args, **kwargs)


class Remainder(models.Model):
    remainder_uuid:uuid = models.UUIDField(unique=True, blank=True, null=True)
    title: str = models.CharField(max_length=100)
    body: str = models.TextField()
    alert_time = models.DateTimeField()
    is_over = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)
    is_favourite = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(Profile, on_delete=models.CASCADE)
    extra_fields = models.JSONField(
        blank=True, null=True, default=dict, 
    )  # For any extra fields you want to add

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        # Ensure `alert_time` is timezone-aware and stored in UTC
        if self.alert_time:
            if timezone.is_naive(self.alert_time):
                # Assume naive input is in current system/local timezone (e.g. from admin panel)
                self.alert_time = timezone.make_aware(
                    self.alert_time, timezone.get_current_timezone()
                )
            # Convert to UTC
            self.alert_time = self.alert_time.astimezone(dt_timezone.utc)

        # Compare in UTC
        self.is_over = self.alert_time < timezone.now()

        if not self.remainder_uuid:
            self.remainder_uuid = uuid.uuid4()

        super().save(*args, **kwargs)
        
    # def save(self, *args, **kwargs):
    #     if self.alert_time and timezone.is_naive(self.alert_time):
    #         self.alert_time = timezone.make_aware(
    #             self.alert_time, timezone.get_current_timezone()
    #         )

    #     # Ensure timezone-aware comparison
    #     now_with_offset = timezone.now() + datetime.timedelta(hours=5, minutes=30)

    #     self.is_over = self.alert_time < now_with_offset
    #     if not self.remainder_uuid:
    #         self.remainder_uuid = uuid.uuid4()
    #     super().save(*args, **kwargs)


class StickyNotes(models.Model):
    stickynotes_uuid:uuid = models.UUIDField(unique=True, blank=True, null=True)
    title: str = models.CharField(max_length=10)
    body: str = models.CharField(max_length=75)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(Profile, on_delete=models.CASCADE)
    extra_fields = models.JSONField(
        blank=True, null=True, default=dict, 
    )  # For any extra fields you want to add

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        if not self.stickynotes_uuid:
            self.stickynotes_uuid = uuid.uuid4()
    #     if not self.updated_at:
    #         self.updated_at = timezone.now() + timezone.timedelta(hours=5, minutes=30)
        super().save(*args, **kwargs)


class Activity(models.Model):
    activity_uuid:uuid = models.UUIDField(unique=True, blank=True, null=True)
    title: str = models.CharField(max_length=100)
    body: str = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(Profile, on_delete=models.CASCADE)
    extra_fields = models.JSONField(
        blank=True, null=True, default=dict, 
    )  # For any extra fields you want to add

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        if not self.activity_uuid:
            self.activity_uuid = uuid.uuid4()
    #     if not self.updated_at:
    #         self.updated_at = timezone.now() + timezone.timedelta(hours=5, minutes=30)
        super().save(*args, **kwargs)


class Todo(models.Model):
    todo_uuid:uuid = models.UUIDField(unique=True, blank=True, null=True)
    title: str = models.CharField(max_length=200)
    is_completed: bool = models.BooleanField(default=False)
    completed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(Profile, on_delete=models.CASCADE)
    extra_fields = models.JSONField(blank=True, null=True, default=dict)

    def __str__(self) -> str:
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.todo_uuid:
            self.todo_uuid = uuid.uuid4()
        super().save(*args, **kwargs)
        
    class Meta:
        ordering = ["-is_completed"]
