#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Maio de 2019
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from .models import PFEUser, Aluno
#from .models import Professor, Parceiro

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
