import datetime

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from django.forms import ModelForm

from users.models import Aluno, Professor, Funcionario

class AlunoForm(forms.Form):
    nascimento = forms.DateField(help_text="Digite sua data de nascimento.")

    def clean_nascimento(self):
        data = self.cleaned_data['nascimento']
        
        # Check if a date is not in the past. 
        if data > datetime.date.today():
            raise ValidationError(_('Data invalida - voce nao nasceu no futuro'))

        # Check if a date is in the allowed range (+4 weeks from today).
        if data.year < 1900:
            raise ValidationError(_('VoTem certeza que e tao velho assim ?'))

        # Remember to always return the cleaned data.
        return data



class AlunoForm2(ModelForm):

    def clean_nascimento(self):
        data = self.cleaned_data['nascimento']
       
        # Check if a date is not in the past. 
        if data > datetime.date.today():
            raise ValidationError(_('Data invalida - voce nao nasceu no futuro'))

        # Check if a date is in the allowed range (+4 weeks from today).
        if data.year < 1900:
            raise ValidationError(_('VoTem certeza que e tao velho assim ?'))

        # Remember to always return the cleaned data.
        return data

    class Meta:
        model = Aluno
        #fields = ['nascimento', 'username', 'email' ]
        fields = '__all__'
        #labels = {'nascimento': _('Renewal date')}
        #help_texts = {'nascimento': _('Enter a date between now and 4 weeks (default 3).')}