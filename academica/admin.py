from django.contrib import admin
import django.contrib.admin.options as admin_opt

from .models import Composicao, Peso, Exame, CodigoColuna, ExibeNota


def dup_peso(modeladmin: admin_opt.ModelAdmin, request, queryset):
    """Função abaixo permite duplicar entradas no banco de dados."""
    # Usada em Eventos e Avisos
    for obj in queryset:
        from_id = obj.id
        obj.id = None
        obj.save()
        message = "duplicando de {} para {}".format(from_id, obj.id)
        modeladmin.log_addition(request=request, object=obj, message=message)

dup_peso.short_description = "Duplicar Entrada(s)"


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
    list_filter = ("composicao", "objetivo")
    search_fields = ["composicao__exame__titulo",]
    actions = [dup_peso]

@admin.register(CodigoColuna)
class CodigoColunaAdmin(admin.ModelAdmin):
    """Código da Coluna do Blackborad."""
    list_display = ("exame", "ano", "semestre", "coluna")

@admin.register(ExibeNota)
class ExibeNotaAdmin(admin.ModelAdmin):
    """Exibe Nota para Estudantes."""
    list_display = ("exame", "ano", "semestre", "exibe")
