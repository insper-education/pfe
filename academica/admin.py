from django.contrib import admin

from .models import Composicao, Peso, Exame


@admin.register(Exame)
class ExameAdmin(admin.ModelAdmin):
    """Peso."""
    list_display = ("titulo", "sigla", "grupo",)

@admin.register(Composicao)
class ComposicaoAdmin(admin.ModelAdmin):
    """Composicao."""
    list_display = ("exame", "tipo_documento", "evento", "entregavel", "data_inicial", "data_final")
    list_filter = ("exame", "tipo_documento", "evento")


@admin.register(Peso)
class PesoAdmin(admin.ModelAdmin):
    """Peso."""
    list_display = ("composicao", "objetivo", "peso",)

