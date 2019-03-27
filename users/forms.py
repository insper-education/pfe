from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from .models import PFEUser, Aluno, Professor, Funcionario

class PFEUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm):
        model = PFEUser
        fields = ('username', 'email')

class PFEUserChangeForm(UserChangeForm):
    class Meta:
        model = PFEUser
        fields = ('username', 'email')

class PFEUserForm(forms.ModelForm):
    class Meta:
        model = PFEUser
        fields = ('first_name', 'last_name', 'email')

class AlunoForm(forms.ModelForm):
    class Meta:
        model = Aluno
        fields = ('curso', 'nascimento', 'local_de_origem')
