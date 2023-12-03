from django.contrib import admin

from .models import TipoDocumento


@admin.register(TipoDocumento)
class TipoDocumentoAdmin(admin.ModelAdmin):
    """Tipo Documento."""
    list_display = ("nome", "projeto", "gravar", "arquivo", "link")
