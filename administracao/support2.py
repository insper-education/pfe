#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 23 de Janeiro de 2025
"""

from projetos.resources import *

from projetos.models import Feedback
from estudantes.models import Relato, Pares


def get_resource(model_class, field_names=None):

    if model_class == Disciplina:
        return get_DisciplinasResource(field_names)
    elif model_class == Aluno:
        return get_EstudantesResource(field_names)
    elif model_class == Avaliacao2:
        return get_Avaliacoes2Resource(field_names)
    elif model_class == Projeto:
        return get_ProjetosResource(field_names)

    else:
        
        bases = (resources.ModelResource,)
        class DynamicResource(*bases):
            class Meta:
                model = model_class
                if field_names:
                    fields = tuple(field_names)
        
        return DynamicResource()


def get_queryset(resource, model_class, ano, semestre):

    if resource is None:
        return None
    
    queryset = None
    if model_class == Projeto:
        queryset = resource._meta.model.objects.filter(ano=ano, semestre=semestre)
    elif model_class == Aluno:
        queryset = resource._meta.model.objects.filter(ano=ano, semestre=semestre)
    elif model_class == Proposta:
        queryset = resource._meta.model.objects.filter(ano=ano, semestre=semestre)
    elif model_class == Alocacao or model_class == Avaliacao2:
        queryset = resource._meta.model.objects.filter(projeto__ano=ano, projeto__semestre=semestre)
    elif model_class == Pares:
        queryset = resource._meta.model.objects.filter(alocacao_de__projeto__ano=ano, alocacao_de__projeto__semestre=semestre)
    elif model_class == Relato:
        queryset = resource._meta.model.objects.filter(alocacao__projeto__ano=ano, alocacao__projeto__semestre=semestre)
    elif model_class == Opcao:
        queryset = resource._meta.model.objects.filter(proposta__ano=ano, proposta__semestre=semestre)
    elif model_class == Feedback:
        if str(semestre) == '1':
            faixa = [str(ano)+"-01-01", str(ano)+"-05-31"]
        else:
            faixa = [str(ano)+"-06-01", str(ano)+"-12-31"]
        queryset = resource._meta.model.objects.filter(data__range=faixa)

    if queryset is None:
        queryset = resource._meta.model.objects.all()
    
    return queryset
