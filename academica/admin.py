from django.contrib import admin
import django.contrib.admin.options as admin_opt

from .models import Composicao, Peso, Exame, CodigoColuna, ExibeNota


def dup_peso(modeladmin: admin_opt.ModelAdmin, request, queryset):
    """Função abaixo permite duplicar entradas no banco de dados."""
    for obj in queryset:
        from_id = obj.id
        obj.id = None
        obj.save()
        message = "duplicando de {} para {}".format(from_id, obj.id)
        modeladmin.log_addition(request=request, object=obj, message=message)

dup_peso.short_description = "Duplicar Entrada(s)"


def dup_composicao(modeladmin: admin_opt.ModelAdmin, request, queryset):
    """Função abaixo permite duplicar entradas no banco de dados."""
    for obj in queryset:
        from_id = obj.id
        obj.id = None
        obj.save()
        message = "duplicando de {} para {}".format(from_id, obj.id)
        modeladmin.log_addition(request=request, object=obj, message=message)

dup_composicao.short_description = "Duplicar Entrada(s)"


@admin.register(Exame)
class ExameAdmin(admin.ModelAdmin):
    """Exame."""
    list_display = ("titulo", "titulo_en", "sigla", "grupo", "periodo_para_rubricas")

@admin.register(Composicao)
class ComposicaoAdmin(admin.ModelAdmin):
    """Composicao."""
    list_display = ("exame", "tipo_documento", "evento", "entregavel", "data_inicial", "data_final")
    list_filter = ("exame", "tipo_documento", "evento")
    search_fields = ["exame__titulo",]
    actions = [dup_composicao]

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
