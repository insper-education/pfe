#!/usr/bin/env python

"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 14 de Novembro de 2019
"""

from django.contrib import admin
#from django.contrib.admin import SimpleListFilter
import django.contrib.admin.options as admin_opt
from django.db import IntegrityError
from django.utils.text import slugify

from .models import *



def dup_entrada(modeladmin: admin_opt.ModelAdmin, request, queryset):
    """Função abaixo permite duplicar entradas no banco de dados."""
    for obj in queryset:
        from_id = obj.id
        obj.id = None

        # Handle unique fields
        for field in obj._meta.get_fields():
            if getattr(field, 'unique', False) and hasattr(obj, field.name):
                value = getattr(obj, field.name)
                ModelClass = obj.__class__
                field_name = field.name

                # Only try to make a unique value for CharField/TextField
                if hasattr(field, 'get_internal_type') and field.get_internal_type() in ['CharField', 'TextField']:
                    if value is None:
                        value = ""
                    max_length = getattr(field, 'max_length', None)
                    base_value = str(value)
                    suffix = " (Cópia)"
                    # If suffix is too long, use a shorter one
                    if max_length is not None and len(suffix) >= max_length:
                        suffix = "C"
                    # Truncate base_value if needed
                    if max_length is not None:
                        available = max_length - len(suffix)
                        if available < 1:
                            available = 1  # Always leave at least 1 char
                        base_value = base_value[:available]
                    new_value = f"{base_value}{suffix}"
                    counter = 2
                    while ModelClass.objects.filter(**{field_name: new_value}).exists():
                        suffix_counter = f" ({counter})"
                        # If suffix_counter is too long, use just the number
                        if max_length is not None and len(suffix_counter) >= max_length:
                            suffix_counter = str(counter)
                        if max_length is not None:
                            available = max_length - len(suffix_counter)
                            if available < 1:
                                available = 1
                            base_value = str(value)[:available]
                        new_value = f"{base_value}{suffix_counter}"
                        counter += 1
                    setattr(obj, field.name, new_value)
                else:
                    # For non-string unique fields, set to None if possible
                    try:
                        setattr(obj, field.name, None)
                    except Exception:
                        pass  # If field cannot be None, let save() fail and show error

        try:
            obj.save()
            message = "duplicando de {} para {}".format(from_id, obj.id)
            modeladmin.log_addition(request=request, object=obj, message=message)
        except IntegrityError as e:
            modeladmin.message_user(request, f"Erro ao duplicar {from_id}: {e}", level="error")
        except Exception as e:
            modeladmin.message_user(request, f"Erro ao duplicar {from_id}: {e}", level="error")

dup_entrada.short_description = "Duplicar Entrada(s)"


@admin.register(Carta)
class CartaAdmin(admin.ModelAdmin):
    """Definição do que aparece no sistema de administração do Django."""
    list_display = ("template", "sigla")
    ordering = ("template",)
    search_fields = ["template", "texto"]
    actions = [dup_entrada]

@admin.register(GrupoCertificado)
class GrupoCertificadoAdmin(admin.ModelAdmin):
    """Definição do que aparece no sistema de administração do Django."""
    list_display = ("nome", "sigla", "cor")
    ordering = ("nome",)
    search_fields = ["nome", "sigla"]


@admin.register(TipoCertificado)
class TipoCertificadoAdmin(admin.ModelAdmin):
    """Definição do que aparece no sistema de administração do Django."""
    list_display = ("titulo", "sigla", "grupo_certificado", "exame")
    ordering = ("titulo",)
    search_fields = ["titulo", "sigla"]


@admin.register(TipoEvento)
class TipoEventoAdmin(admin.ModelAdmin):
    """Definição do que aparece no sistema de administração do Django."""
    list_display = ("nome", "sigla", "cor")
    ordering = ("nome",)
    search_fields = ["nome", "sigla"]


@admin.register(Despesa)
class DespesaAdmin(admin.ModelAdmin):
    """Definição do que aparece no sistema de administração do Django."""   
    list_display = ("descricao", "data", "valor_r", "valor_d")
    ordering = ("data",)
    search_fields = ["descricao", "fornecedor", "projeto"]
    list_filter = ["data"]


@admin.register(Estrutura)
class EstruturaAdmin(admin.ModelAdmin):
    """Definição do que aparece no sistema de administração do Django."""   
    list_display = ("nome", "sigla",)
    ordering = ("nome",)
    search_fields = ["nome", "sigla", "descricao", "json",]
    actions = [dup_entrada]
    