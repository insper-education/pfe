from django.contrib import admin

from .models import Composicao, Peso, Exame, CodigoColuna, ExibeNota


@admin.register(Exame)
class ExameAdmin(admin.ModelAdmin):
    """Exame."""
    list_display = ("titulo", "sigla", "grupo", "periodo_para_rubricas")


@admin.register(Composicao)
class ComposicaoAdmin(admin.ModelAdmin):
    """Composicao."""
    list_display = ("exame", "tipo_documento", "evento", "entregavel", "data_inicial", "data_final")
    ordering = ("data_inicial",)
    list_filter = ("exame", "tipo_documento", "evento")

@admin.register(Peso)
class PesoAdmin(admin.ModelAdmin):
    """Peso."""
    list_display = ("composicao", "objetivo", "peso")
    list_filter = ("objetivo",)
    search_fields = ["composicao__exame__titulo",]

@admin.register(CodigoColuna)
class CodigoColunaAdmin(admin.ModelAdmin):
    """Código da Coluna do Blackborad."""
    list_display = ("exame", "ano", "semestre", "coluna")

@admin.register(ExibeNota)
class ExibeNotaAdmin(admin.ModelAdmin):
    """Exibe Nota para Estudantes."""
    list_display = ("exame", "ano", "semestre", "exibe")
