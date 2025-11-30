from django import forms
from django.core.exceptions import ValidationError

from projetos.models import Organizacao


class PropostaForm(forms.Form):
    """Form para submissão/edição de proposta (campos usados nesta view)."""
    titulo_prop = forms.CharField(required=True, max_length=300, widget=forms.TextInput(attrs={"placeholder": "Título da proposta"}))
    internacional = forms.BooleanField(required=False)
    intercambio = forms.BooleanField(required=False)
    empreendendo = forms.BooleanField(required=False)
    colaboracao = forms.ModelChoiceField(required=False, queryset=Organizacao.objects.all(), empty_label="-- selecione --")
    mensagem = forms.BooleanField(required=False)
    arquivo = forms.FileField(required=False)

    def clean_titulo_prop(self):
        titulo = (self.cleaned_data.get("titulo_prop") or "").strip()
        # Deixa opcional: só exigido para criação (validado na view)
        return titulo or ""

    def clean_arquivo(self):
        arquivo = self.cleaned_data.get("arquivo")
        # Valida apenas tipo básico aqui; restrições específicas continuam no helper
        if arquivo and hasattr(arquivo, 'content_type'):
            if not (arquivo.content_type in {"application/pdf", "application/octet-stream"} or arquivo.name.lower().endswith(".pdf")):
                raise ValidationError("Arquivo deve ser PDF.")
        return arquivo
