from django.contrib import admin

# Register your models here.

from .models import PerguntasRespostas

@admin.register(PerguntasRespostas)
class PerguntasRespostasAdmin(admin.ModelAdmin):
    """Definição do que aparece no sistema de administração do Django."""

    list_display = ("proposta", "pergunta", "resposta", "data_pergunta", "data_resposta", "quem_perguntou", "quem_respondeu")