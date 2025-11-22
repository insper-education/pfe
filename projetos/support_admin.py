#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 22 de Novembro de 2025
"""

from datetime import timedelta
from django.contrib.admin import SimpleListFilter
import django.contrib.admin.options as admin_opt

from .models import Configuracao

def dup_projeto(modeladmin: admin_opt.ModelAdmin, request, queryset):
    """Função abaixo permite duplicar entradas no banco de dados."""
    for obj in queryset:
        from_id = obj.id
        obj.id = None
        if Configuracao.objects.get().semestre == 1:
            obj.semestre = 2
            obj.ano = Configuracao.objects.get().ano
        else:
            obj.semestre = 1
            obj.ano = Configuracao.objects.get().ano + 1
        obj.save()
        message = "duplicando de {} para {}".format(from_id, obj.id)
        modeladmin.log_addition(request=request, object=obj, message=message)


dup_projeto.short_description = "Duplicar Entrada(s)"


def dup_entrada(modeladmin: admin_opt.ModelAdmin, request, queryset):
    """Função abaixo permite duplicar entradas no banco de dados."""
    # Usada para duplicar entradas em diversos admin.py
    for obj in queryset:
        from_id = obj.id
        obj.id = None

        # Check for unique fields and append suffix
        for field in obj._meta.get_fields():
            if hasattr(field, "unique") and field.unique and field.name != "id":
                current_value = getattr(obj, field.name, None)
                if current_value:
                    if isinstance(current_value, str):
                        setattr(obj, field.name, f"{current_value}_")
                    else:
                        raise ValueError(f"Cannot duplicate object with non-string unique field: {field.name}")

        obj.save()
        message = "duplicando de {} para {}".format(from_id, obj.id)
        modeladmin.log_addition(request=request, object=obj, message=message)

dup_entrada.short_description = "Duplicar Entrada(s)"


def dup_entrada_182(modeladmin: admin_opt.ModelAdmin, request, queryset):
    """Função abaixo permite duplicar entradas no banco de dados com 182 dias adicionados."""
    for obj in queryset:
        from_id = obj.id
        obj.id = None
        if hasattr(obj, 'startDateTime') and hasattr(obj, 'endDateTime'):
            obj.startDateTime += timedelta(days=182)
            obj.endDateTime += timedelta(days=182)
        elif hasattr(obj, 'startDate') and hasattr(obj, 'endDate'):
            obj.startDate += timedelta(days=182)
            obj.endDate += timedelta(days=182)
        obj.save()
        message = "duplicando de {} para {}".format(from_id, obj.id)
        modeladmin.log_addition(request=request, object=obj, message=message)


dup_entrada_182.short_description = "Duplicar Entrada(s) adicionando 182 dias"


def dup_encontros(modeladmin: admin_opt.ModelAdmin, request, queryset):
    """Função abaixo permite duplicar entradas no banco de dados."""
    for obj in queryset:
        from_id = obj.id
        obj.id = None
        obj.save()
        message = "duplicando de {} para {}".format(from_id, obj.id)
        modeladmin.log_addition(request=request, object=obj, message=message)


dup_encontros.short_description = "Duplicar Entrada(s)"


def dup_encontros_4x(modeladmin: admin_opt.ModelAdmin, request, queryset):
    """Função abaixo permite duplicar entradas no banco de dados 4 X."""
    for obj in queryset:
        for _ in range(4):
            from_id = obj.id
            obj.id = None
            obj.save()
            message = "duplicando de {} para {}".format(from_id, obj.id)
            modeladmin.log_addition(request=request, object=obj, message=message)


dup_encontros_4x.short_description = "Duplicar Entrada(s) 4 X"


def dup_encontros_8x(modeladmin: admin_opt.ModelAdmin, request, queryset):
    """Função abaixo permite duplicar entradas no banco de dados 8 X."""
    for obj in queryset:
        for _ in range(8):
            from_id = obj.id
            obj.id = None
            obj.save()
            message = "duplicando de {} para {}".format(from_id, obj.id)
            modeladmin.log_addition(request=request, object=obj, message=message)


dup_encontros_8x.short_description = "Duplicar Entrada(s) 8 X"


class FechadoFilter(SimpleListFilter):
    """Para filtrar projetos fechados."""

    title = "Projetos Fechados"
    parameter_name = ""

    def lookups(self, request, model_admin):
        return [
            ("fechados", "Fechados"),
            ("not_fechados", "Não Fechados"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "fechados":
            return queryset.distinct().filter(alocacao__isnull=False)
        if self.value():
            return queryset.distinct().filter(alocacao__isnull=True)
        return None
    

class AnoSemestreFilter(SimpleListFilter):
    """Para filtrar projetos por ano e semestre."""

    title = "Ano/Semestre"
    parameter_name = ""

    def lookups(self, request, model_admin):
        opcoes = []
        for ano in range(2018, Configuracao.objects.get().ano+2):
            for semestre in range(1, 3):
                opcoes.append(("{0}.{1}".format(ano, semestre), "{0}.{1}".format(ano, semestre)))
        return opcoes

    def queryset(self, request, queryset):
        if self.value():
            q_aluno = queryset.distinct().filter(usuario__aluno__ano=int(self.value().split('.')[0]),
                                                 usuario__aluno__semestre=int(self.value().split('.')[1]))
            q_proposta = queryset.distinct().filter(proposta__ano=int(self.value().split('.')[0]),
                                                    proposta__semestre=int(self.value().split('.')[1]))
            
            return q_aluno | q_proposta
                                                    
        return queryset.distinct().all()


class EventoFilter(SimpleListFilter):
    """Para filtrar eventos por semestre."""

    title = "Publico/Semestre"
    parameter_name = ""

    def lookups(self, request, model_admin):
        opcoes = [
            ("academicos", "Acadêmicos"),
            ("coordenacao", "Coordenação"),
        ]
        for ano in range(2018, Configuracao.objects.get().ano+2):
            for semestre in range(1, 3):
                opcoes.append(("{0}.{1}".format(ano, semestre), "{0}.{1}".format(ano, semestre)))
        return opcoes

    def queryset(self, request, queryset):
        if self.value():
            if self.value() == "academicos":
                return queryset.distinct().filter(tipo_evento__coodenacao=False)
            if self.value() == "coordenacao":
                return queryset.distinct().filter(tipo_evento__coodenacao=True)
            if self.value().split(".")[1] == "1":
                return queryset.distinct().filter(startDate__year=int(self.value().split('.')[0]),
                                                  startDate__month__lte=7)
            else:
                return queryset.distinct().filter(startDate__year=int(self.value().split('.')[0]),
                                                  startDate__month__gt=7)
        return queryset.distinct().all()
