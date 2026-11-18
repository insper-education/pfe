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
        if not arquivo:
            return arquivo
        
        # Define tipos MIME e extensões aceitas
        tipos_mime_aceitos = {
            "text/plain",
            "application/pdf",
            "application/zip",
            "application/x-zip",
            "application/x-zip-compressed",
            "application/x-rar-compressed",
            "application/x-7z-compressed",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-powerpoint",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        }
        
        extensoes_aceitas = {".zip", ".rar", ".7zip", ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".mkv", ".mp4", ".avi", ".webm", ".m4v"}
        
        nome_arquivo = arquivo.name.lower()
        extensao = None
        for ext in extensoes_aceitas:
            if nome_arquivo.endswith(ext):
                extensao = ext
                break
        
        content_type = getattr(arquivo, 'content_type', '')
        
        # Verifica se é tipo MIME aceito ou imagem/vídeo genérico
        eh_tipo_mime_aceito = content_type in tipos_mime_aceitos or \
                              content_type.startswith('image/') or \
                              content_type.startswith('video/') or \
                              content_type == 'application/octet-stream'
        
        # Se nem tipo MIME nem extensão foram aceitos, levanta erro
        if not (eh_tipo_mime_aceito or extensao):
            raise ValidationError(
                "Tipo de arquivo não permitido. Aceitos: imagens, vídeos, documentos, "
                "arquivos compactados (ZIP, RAR, 7Z) e documentos Office."
            )
        
        return arquivo
