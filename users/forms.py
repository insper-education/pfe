from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import PFEUser

class PFEUserCreationForm(UserCreationForm):

    class Meta(UserCreationForm):
        model = PFEUser
        fields = ('username', 'email')

class PFEUserChangeForm(UserChangeForm):

    class Meta:
        model = PFEUser
        fields = ('username', 'email')


