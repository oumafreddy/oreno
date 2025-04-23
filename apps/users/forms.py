# apps/users/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser, Profile

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('email', 'username', 'organization', 'role')
        widgets = {
            'organization': forms.Select(attrs={'class': 'form-select'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
        }


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ('email', 'username', 'organization', 'role')
        widgets = {
            'organization': forms.Select(attrs={'class': 'form-select'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
        }


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('avatar',)
        widgets = {
            'avatar': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        }
