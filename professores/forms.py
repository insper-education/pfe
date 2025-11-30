from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError

from projetos.models import Projeto, TematicaEncontro
from users.models import PFEUser


class DinamicasForm(forms.Form):
    """Formulário para criação e edição de dinâmicas (Encontros)."""
    inicio = forms.DateTimeField(input_formats=["%Y-%m-%dT%H:%M", "%d/%m/%Y, %H:%M"], required=True)
    fim = forms.DateTimeField(input_formats=["%Y-%m-%dT%H:%M", "%d/%m/%Y, %H:%M"], required=True)
    vezes = forms.IntegerField(min_value=1, initial=1, required=False)
    intervalo = forms.IntegerField(min_value=0, initial=0, required=False)  # minutos
    local = forms.CharField(max_length=255, required=False)
    tematica = forms.IntegerField(required=False)
    projeto = forms.IntegerField(required=False)
    facilitador = forms.IntegerField(required=False)

    def clean_tematica(self):
        """Converte ID para objeto TematicaEncontro."""
        tematica_id = self.cleaned_data.get('tematica')
        if not tematica_id or tematica_id == 0:
            return None
        try:
            return TematicaEncontro.objects.get(id=tematica_id)
        except TematicaEncontro.DoesNotExist:
            raise ValidationError("Temática não encontrada.")

    def clean_projeto(self):
        """Converte ID para objeto Projeto."""
        projeto_id = self.cleaned_data.get('projeto')
        if not projeto_id or projeto_id == 0:
            return None
        try:
            return Projeto.objects.get(id=projeto_id)
        except Projeto.DoesNotExist:
            raise ValidationError("Projeto não encontrado.")

    def clean_facilitador(self):
        """Converte ID para objeto PFEUser."""
        facilitador_id = self.cleaned_data.get('facilitador')
        if not facilitador_id or facilitador_id == 0:
            return None
        try:
            return PFEUser.objects.get(id=facilitador_id)
        except PFEUser.DoesNotExist:
            raise ValidationError("Facilitador não encontrado.")

    def clean(self):
        cleaned = super().clean()
        inicio = cleaned.get("inicio")
        fim = cleaned.get("fim")
        if inicio and fim and fim <= inicio:
            self.add_error("fim", "Fim deve ser depois de início.")

        # Garantir que os datetimes sejam aware no timezone atual
        tz = timezone.get_current_timezone()
        if inicio and timezone.is_naive(inicio):
            cleaned["inicio"] = timezone.make_aware(inicio, tz)
        if fim and timezone.is_naive(fim):
            cleaned["fim"] = timezone.make_aware(fim, tz)
        return cleaned


class EncontroFeedbackForm(forms.Form):
    """Formulário para feedback de mentorias/encontros."""
    observacoes_estudantes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 8, 'cols': 100}),
        max_length=5000,
        required=False,
        label="Observações dos Estudantes"
    )
    observacoes_orientador = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 8, 'cols': 100}),
        max_length=5000,
        required=False,
        label="Observações para o Orientador"
    )

    def clean(self):
        cleaned = super().clean()
        obs_estudantes = cleaned.get("observacoes_estudantes", "").strip()
        obs_orientador = cleaned.get("observacoes_orientador", "").strip()
        
        # Pelo menos um campo deve ser preenchido
        if not obs_estudantes and not obs_orientador:
            raise ValidationError("Pelo menos uma observação deve ser preenchida.")
        
        return cleaned
