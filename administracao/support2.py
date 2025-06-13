#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 23 de Janeiro de 2025
"""

from projetos.resources import *

# def get_resource(dado):
#     resource_map = {
#         "disciplinas": DisciplinasResource,
#         "estudantes": EstudantesResource,
#         "avaliacoes": Avaliacoes2Resource,
#         "projetos": ProjetosResource,
#         "organizacoes": OrganizacoesResource,
#         "opcoes": OpcoesResource,
#         "usuarios": UsuariosResource,
#         "professores": ProfessoresResource,
#         "parceiros": ParceirosResource,
#         "configuracao": ConfiguracaoResource,
#         "feedbacks": FeedbacksResource,
#         "alocacoes": AlocacoesResource,
#         "pares": ParesResource,
#         "objetivos": ObjetivosDeAprendizagemResource,
#         "relatos": RelatosResource,
#         "areas_interesse": AreaDeInteresseResource,
#         "propostas": PropostasResource,
#     }
#     return resource_map.get(dado, None)()  # Função precisa ser chamada para criar o objeto


def get_resource(model_name, fields=None):

    # Disciplina está com um processo diferente, validar o porque
    if model_name=="disciplinas":
        return DisciplinasResource()
    elif model_name == "estudantes":
        return EstudantesResource()
    elif model_name == "avaliacoes":
        return Avaliacoes2Resource()
    elif model_name == "projetos":
        return ProjetosResource()

    else:
        resource_map = {
            # "disciplinas": DisciplinasResource,
            # "estudantes": EstudantesResource,
            # "avaliacoes": Avaliacoes2Resource,
            # "projetos": ProjetosResource,
            "organizacoes": Organizacao,
            "opcoes": Opcao,
            "usuarios": PFEUser,
            "professores": Professor,
            "parceiros": Parceiro,
            "configuracao": Configuracao,
            "feedbacks": Feedback,
            "alocacoes": Alocacao,
            "pares": Pares,
            "objetivos": ObjetivosDeAprendizagem,
            "relatos": Relato,
            "areas_interesse": AreaDeInteresse,
            "propostas": Proposta,
        }
        
        model_class = resource_map.get(model_name, None)

        class DynamicResource(resources.ModelResource):
            class Meta:
                model = model_class
                # if fields:
                #     fields = tuple(fields)

        
        return DynamicResource()


def get_queryset(resource, dado, ano, semestre):

    if resource is None:
        return None
    
    queryset = None
    if dado == "projetos":
        queryset = resource._meta.model.objects.filter(ano=ano, semestre=semestre)
    elif dado == "estudantes":
        queryset = resource._meta.model.objects.filter(ano=ano, semestre=semestre)
    elif dado == "propostas":
        queryset = resource._meta.model.objects.filter(ano=ano, semestre=semestre)
    elif dado == "alocacoes" or dado == "avaliacoes":
        queryset = resource._meta.model.objects.filter(projeto__ano=ano, projeto__semestre=semestre)
    elif dado == "pares":
        queryset = resource._meta.model.objects.filter(alocacao_de__projeto__ano=ano, alocacao_de__projeto__semestre=semestre)
    elif dado == "relatos":
        queryset = resource._meta.model.objects.filter(alocacao__projeto__ano=ano, alocacao__projeto__semestre=semestre)
    elif dado == "opcoes":
        queryset = resource._meta.model.objects.filter(proposta__ano=ano, proposta__semestre=semestre)
    elif dado == "feedbacks":
        if semestre == '1':
            faixa = [ano+"-01-01", ano+"-05-31"]
        else:
            faixa = [ano+"-06-01", ano+"-12-31"]
        queryset = resource._meta.model.objects.filter(data__range=faixa)

    if queryset is None:
        queryset = resource._meta.model.objects.all()
    
    return queryset
