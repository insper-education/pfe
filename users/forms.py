#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Maio de 2019
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from .models import PFEUser, Aluno


class PFEUserCreationForm(UserCreationForm):
    """Form para criação de PFEUser."""

    class Meta(UserCreationForm):
        """Meta para UserCreationForm."""

        model = PFEUser
        fields = ("username", "email")


class PFEUserChangeForm(UserChangeForm):
    """Form para trocar de PFEUser."""

    class Meta:
        """Meta para PFEUserChangeForm."""

        model = PFEUser
        fields = ("username", "email")


class PFEUserForm(forms.ModelForm):
    """Form para PFEUser."""

    class Meta:
        """Meta para PFEUserForm."""

        model = PFEUser
        fields = ("first_name", "last_name", "email")


class AlunoForm(forms.ModelForm):
    """Form para Aluno."""

    class Meta:
        """Meta para AlunoForm."""

        model = Aluno
        fields = ("matricula",)
