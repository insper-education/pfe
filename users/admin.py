from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from .forms import PFEUserCreationForm, PFEUserChangeForm
from .models import PFEUser

class PFEUserAdmin(UserAdmin):
    add_form = PFEUserCreationForm
    form = PFEUserChangeForm
    model = PFEUser
    list_display = ['email', 'username',]

admin.site.register(PFEUser, PFEUserAdmin)

