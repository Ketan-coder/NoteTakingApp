import datetime
from django.db import models
from ckeditor.fields import RichTextField
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone
from Users.models import Profile
from django.contrib import messages

# PRIORITY_LIST = [
#     ('Important','Important'),
#     ('Not Important','Not Important'),
# ]
# Create your models here.
class Notebook(models.Model):
    title:str = models.CharField(max_length=100)
    body:str = models.TextField()
    priority = models.IntegerField(default=0)
    # priority = models.CharField(choices=PRIORITY_LIST,default="Important",max_length=50)
    is_favourite = models.BooleanField(default=False)
    is_shared = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_password_protected:bool = models.BooleanField(default=False)
    is_password_entered:bool = models.BooleanField(default=False)
    is_accessed_recently:bool = models.BooleanField(default=False)
    password = models.CharField(max_length=20, blank=True, null=True,help_text="Enter the password to access this page")
    author = models.ForeignKey(Profile, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.title
    
    def save(self, *args, **kwargs):
        if self.is_password_protected and not self.password:
            raise ValueError("Password is required for password-protected notebooks.")
        super().save(*args, **kwargs)

    def check_password(self, password) -> bool:
        if self.password == password:
            return True
        else:
            return False
    
class SharedNotebook(models.Model):
    notebook = models.OneToOneField(Notebook, on_delete=models.CASCADE)
    owner = models.ForeignKey(Profile, on_delete=models.CASCADE,related_name='notebook_owner')
    sharedTo = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='shared_to', blank=True, null=True)
    shared_at = models.DateTimeField(auto_now_add=True)
    shareable_link = models.URLField(blank=True, null=True)
    can_edit = models.BooleanField(default=False)

    def save(self, request=None, *args, **kwargs):
        if not self.shared_at:
            self.shared_at = timezone.now() + timezone.timedelta(hours=5, minutes=30)
        
        if not self.shareable_link:
            self.shareable_link = f'sharedNotebooks/{self.notebook.id}/'

        if request:
            messages.success(request, f'Notebook shared successfully! Here is the link to view it: {self.shareable_link}')

        notebook = self.notebook
        notebook.is_shared = True
        notebook.save()
        
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        owner_name = self.notebook.author.firstName if self.notebook.author else self.username
        # shared_to_name = self.sharedTo.firstName if self.sharedTo.email else "Unknown"
        return f"{owner_name} shared this - {self.notebook.title}'s Notebook =>  Unkown"
    
class Page(models.Model):
    notebook = models.ForeignKey(Notebook, on_delete=models.CASCADE)
    title:str = models.CharField(max_length=100)
    body:str = models.TextField()
    # is_favourite = models.BooleanField(default=False)
    order = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(Profile, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.notebook.title + " " + self.title
    
    class Meta:
        ordering = ['order']

    def save(self, *args, **kwargs):
        if self.order is None:  # Only assign order if not provided
            last_page = self.notebook.pages.order_by('-order').first()
            self.order = (last_page.order + 1) if last_page else 1  # Get next order for this notebook
        super().save(*args, **kwargs)
    
    # def save(self, *args, **kwargs):
    #     if not self.updated_at:
    #         self.updated_at = timezone.now() + timezone.timedelta(hours=5, minutes=30)
    #     super().save(*args, **kwargs)

class SubPage(models.Model):
    notebook = models.ForeignKey(Notebook, on_delete=models.CASCADE)
    page = models.ForeignKey(Page, on_delete=models.CASCADE)
    title:str = models.CharField(max_length=100)
    body:str = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(Profile, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.page.title + " " + self.title
    
    # def save(self, *args, **kwargs):
    #     if not self.updated_at:
    #         self.updated_at = timezone.now() + timezone.timedelta(hours=5, minutes=30)
    #     super().save(*args, **kwargs)
    
class Remainder(models.Model):
    title:str = models.CharField(max_length=100)
    body:str = models.TextField()
    alert_time = models.DateTimeField()
    is_over = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)
    is_favourite = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(Profile, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.title
    
    # def save(self, *args, **kwargs):
    #     # if not self.updated_at:
    #     #     self.updated_at = timezone.now() + timezone.timedelta(hours=5, minutes=30)
    #     if self.alert_time < timezone.now() + datetime.timedelta(hours=5, minutes=30):
    #         self.is_over = True
    #     else:
    #         self.is_over = False
    #     super().save(*args, **kwargs)
    def save(self, *args, **kwargs):
        if self.alert_time and timezone.is_naive(self.alert_time):
            self.alert_time = timezone.make_aware(self.alert_time, timezone.get_current_timezone())

        # Ensure timezone-aware comparison
        now_with_offset = timezone.now() + datetime.timedelta(hours=5, minutes=30)
        
        self.is_over = self.alert_time < now_with_offset
        
        super().save(*args, **kwargs)
    
class StickyNotes(models.Model):
    title:str = models.CharField(max_length=10)
    body:str = models.CharField(max_length=75)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(Profile, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.title
    
    # def save(self, *args, **kwargs):
    #     if not self.updated_at:
    #         self.updated_at = timezone.now() + timezone.timedelta(hours=5, minutes=30)
    #     super().save(*args, **kwargs)

class Activity(models.Model):
    title:str = models.CharField(max_length=100)
    body:str = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(Profile, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.title
    
    # def save(self, *args, **kwargs):
    #     if not self.updated_at:
    #         self.updated_at = timezone.now() + timezone.timedelta(hours=5, minutes=30)
    #     super().save(*args, **kwargs)