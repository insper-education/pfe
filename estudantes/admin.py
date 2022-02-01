from django.contrib import admin

from .models import Relato

@admin.register(Relato)
class RelatoAdmin(admin.ModelAdmin):
    """Exibição no sistema de administração do Django para Relato."""

    list_display = ("momento", "alocacao", "texto", "avaliacao")
    list_filter = ("momento",)
    search_fields = ["alocacao",]
