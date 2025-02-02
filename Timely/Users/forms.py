# create a registaretion form
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils.translation import gettext_lazy as _

from .models import Profile

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, validators=[validate_email])

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError(_('Email already exists.'))
        return email

    def save(self, commit=True):
        user = super(UserRegistrationForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user
    
    
class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['firstName', 'lastName', 'bio']