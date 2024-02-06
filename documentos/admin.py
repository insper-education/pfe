from django.contrib import admin

from .models import TipoDocumento


@admin.register(TipoDocumento)
class TipoDocumentoAdmin(admin.ModelAdmin):
    """Tipo Documento."""
    list_display = ("nome", "sigla", "projeto", "gravar", "arquivo", "link",)
    search_fields = ["nome",]
