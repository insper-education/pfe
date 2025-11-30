"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 30 de Novembro de 2025
"""


from django import forms
from django.core.exceptions import ValidationError as DjangoCoreValidationError
from django.utils.text import slugify

from users.models import PFEUser, Aluno


class EstudanteInformacoesForm(forms.Form):
    """Form para informações adicionais do estudante."""
    
    trabalhou = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            "rows": 4,
            "cols": 80,
            "id": "trabalhou",
        })
    )
    
    atividades = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            "rows": 4,
            "cols": 80,
            "id": "atividades",
        })
    )
    
    familia = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            "rows": 4,
            "cols": 80,
            "id": "familia",
        })
    )
    
    TRABALHARA_CHOICES = [
        ("Y", "Sim"),
        ("N", "Não"),
        ("M", "Talvez"),
    ]
    
    trabalhara = forms.ChoiceField(
        required=False,
        choices=TRABALHARA_CHOICES,
        widget=forms.RadioSelect(attrs={"class": "radio-trabalho"})
    )
    
    recrutadores = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={"id": "recrutadores"})
    )
    
    linkedin = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "size": 80,
            "id": "linkedin",
            "placeholder": "https://www.linkedin.com/",
            "pattern": r"\s*(https?://)?(www\.)?linkedin\.com/[^\s]*\s*",
        })
    )
    
    celular = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "size": 20,
            "id": "celular",
            "placeholder": "(XX)XXXX-XXXX",
        })
    )
    
    conta_github = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "size": 38,
            "id": "conta_github",
        })
    )

    def __init__(self, *args, **kwargs):
        vencido = kwargs.pop("vencido", False)
        super().__init__(*args, **kwargs)
        
        # Get max_length from model fields
        try:
            self.fields["trabalhou"].widget.attrs["maxlength"] = (
                Aluno._meta.get_field("trabalhou").max_length
            )
        except Exception:
            pass
            
        try:
            self.fields["atividades"].widget.attrs["maxlength"] = (
                Aluno._meta.get_field("atividades").max_length
            )
        except Exception:
            pass
            
        try:
            self.fields["familia"].widget.attrs["maxlength"] = (
                Aluno._meta.get_field("familia").max_length
            )
        except Exception:
            pass
        
        try:
            max_len = PFEUser._meta.get_field("linkedin").max_length
            # Subtract 7 for "https://" if needed
            self.fields["linkedin"].widget.attrs["maxlength"] = max(max_len - 7, 0)
        except Exception:
            pass
            
        try:
            self.fields["celular"].widget.attrs["maxlength"] = (
                PFEUser._meta.get_field("celular").max_length
            )
        except Exception:
            pass
            
        try:
            self.fields["conta_github"].widget.attrs["maxlength"] = (
                PFEUser._meta.get_field("conta_github").max_length
            )
        except Exception:
            pass
        
        # Disable all fields if deadline passed
        if vencido:
            for field in self.fields.values():
                field.widget.attrs["disabled"] = True

    def clean_linkedin(self):
        link = (self.cleaned_data.get("linkedin") or "").strip()
        if not link:
            return None
        if not link.startswith("http://") and not link.startswith("https://"):
            link = "https://" + link
        # Enforce max length according to PFEUser model field, if defined
        try:
            max_length = PFEUser._meta.get_field("linkedin").max_length
        except Exception:
            max_length = None
        if max_length and len(link) > max_length:
            # Use forms.ValidationError so error attaches to the field
            raise forms.ValidationError(
                f"Link do LinkedIn maior que {max_length} caracteres.")
        return link

    def clean(self):
        cleaned = super().clean()
        # Normalize empties
        for key in [
            "trabalhou", "atividades", "familia", "trabalhara",
            "celular", "conta_github",
        ]:
            val = cleaned.get(key)
            if isinstance(val, str):
                cleaned[key] = val.strip() or None
        return cleaned
