from django.contrib import admin

from .models import Relato, Pares, EstiloComunicacao

@admin.register(Relato)
class RelatoAdmin(admin.ModelAdmin):
    """Exibição no sistema de administração do Django para Relato."""

    list_display = ("momento", "alocacao", "avaliacao")
    list_filter = ("momento",)
    search_fields = ["alocacao__aluno__user__first_name",
                     "alocacao__aluno__user__last_name",
                     "alocacao__aluno__user__username",]

@admin.register(Pares)
class ParesAdmin(admin.ModelAdmin):
    """Exibição no sistema de administração do Django para Avaliação de Pares."""

    list_display = ("momento", "alocacao_de", "alocacao_para")
    list_filter = ("momento", "tipo")
    search_fields = ["alocacao_de__aluno__user__first_name",
                     "alocacao_de__aluno__user__last_name",
                     "alocacao_de__aluno__user__username",
                     "alocacao_para__aluno__user__first_name",
                     "alocacao_para__aluno__user__last_name",
                     "alocacao_para__aluno__user__username",
                     "alocacao_de__projeto__proposta__titulo",
                     ]

@admin.register(EstiloComunicacao)
class EstiloComunicacaoAdmin(admin.ModelAdmin):
    """Exibição no sistema de administração do Django para Avaliação de EstiloComunicacao."""

    list_display = ("bloco", "questao")
