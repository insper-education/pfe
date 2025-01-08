#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Janeiro de 2024
"""

from datetime import date

from .models import Exame

from projetos.models import Documento, Evento, Avaliacao2, Observacao

from users.models import Alocacao, Aluno




def filtra_composicoes(composicoes, ano, semestre):
    """Filtra composições."""
    composicoes = composicoes.exclude(data_final__year__lt=ano)
    composicoes = composicoes.exclude(data_inicial__year__gt=ano)
    
    if semestre == 1:
        composicoes = composicoes.exclude(data_inicial__year=ano, data_inicial__month__gt=6)
    else:
        composicoes = composicoes.exclude(data_final__year=ano, data_final__month__lt=8)

    return composicoes

def get_nota_peso(avaliacoes):
    nota = 0
    peso = 0
    for avaliacao in avaliacoes:
        if avaliacao.peso and avaliacao.peso > 0:
            nota += float(avaliacao.nota)*float(avaliacao.peso)
            peso += float(avaliacao.peso)
    if peso > 0:
        nota = nota/peso
    else:
        nota = 0
    return nota, peso
        
def filtra_entregas(composicoes, projeto, user=None):
    entregas = []

    if projeto.orientador:
        orientador = projeto.orientador.user
    else:
        orientador = None

    for composicao in composicoes:

        evento = Evento.get_evento(tipo=composicao.tipo_evento, ano=projeto.ano, semestre=projeto.semestre)

        if composicao.exame.grupo:
            documentos = Documento.objects.filter(tipo_documento=composicao.tipo_documento,
                                                  projeto=projeto)
            avaliacoes = Avaliacao2.objects.filter(projeto=projeto, 
                                                   exame=composicao.exame, 
                                                   avaliador=orientador)
            nota, peso = get_nota_peso(avaliacoes)
            observacao = Observacao.objects.filter(projeto=projeto,
                                                   exame=composicao.exame,
                                                   avaliador=orientador).last()
            
            entregas.append({"composicao": composicao, 
                            "evento": evento,
                            "documentos": documentos,  
                            "avaliacoes": avaliacoes,
                            "nota": nota,
                            "observacao": observacao,
                            })

        else:

            if user and user.tipo_de_usuario == 1 : # Para o próprio estudante 
                alocacao = Alocacao.objects.get(projeto=projeto, aluno=user.aluno)
                documentos = Documento.objects.filter(tipo_documento=composicao.tipo_documento,
                                                      projeto=projeto,
                                                      usuario=user)
                avaliacoes = Avaliacao2.objects.filter(projeto=projeto, 
                                                       exame=composicao.exame, 
                                                       avaliador=orientador,
                                                       alocacao=alocacao)
                nota, peso = get_nota_peso(avaliacoes)
                observacao = Observacao.objects.filter(projeto=projeto,
                                                       exame=composicao.exame,
                                                       avaliador=orientador,
                                                       alocacao=alocacao).last()
                
                entregas.append({"composicao": composicao, 
                                "evento": evento,
                                "documentos": documentos,  
                                "avaliacoes": avaliacoes,
                                "nota": nota,
                                "observacao": observacao,
                                })

            else: # Todos os integrantes do grupo
                alocacoes = {}

                #  Estudantes externos não são avaliados diretamente
                for alocacao in Alocacao.objects.filter(projeto=projeto, aluno__externo__isnull=True):
                   
                    # alocacao = Alocacao.objects.get(projeto=projeto, aluno=user.aluno)
                    documentos = Documento.objects.filter(tipo_documento=composicao.tipo_documento,
                                                          projeto=projeto, 
                                                          usuario=alocacao.aluno.user)
                    avaliacoes = Avaliacao2.objects.filter(projeto=projeto, 
                                                        exame=composicao.exame, 
                                                        avaliador=orientador,
                                                        alocacao=alocacao)
                    nota, peso = get_nota_peso(avaliacoes)
                    observacao = Observacao.objects.filter(projeto=projeto,
                                                        exame=composicao.exame,
                                                        avaliador=orientador,
                                                        alocacao=alocacao).last()
                    
                    alocacoes[alocacao] = {"documentos": documentos,  
                                           "avaliacoes": avaliacoes,
                                           "nota": nota,
                                           "observacao": observacao,
                                           }
    
                entregas.append({"composicao": composicao, 
                                 "evento": evento,
                                 "alocacoes": alocacoes,
                                })

    entregas = sorted(entregas, key=lambda t: (date.today() if t["evento"] is None else t["evento"].endDate))

    return entregas



def media_falconi(projeto):
    exame = Exame.objects.get(titulo="Falconi")
    aval_banc_falconi = Avaliacao2.objects.filter(projeto=projeto, exame=exame)  # Falc.
    nota_banca_falconi, _, _ = Aluno.get_banca(None, aval_banc_falconi)
    return nota_banca_falconi

def media_bancas(projeto):
    exames = Exame.objects.filter(titulo="Banca Final") | Exame.objects.filter(titulo="Banca Intermediária")
    aval_bancas = Avaliacao2.objects.filter(projeto=projeto, exame__in=exames)  # Bancas.
    nota_bancas, _, _ = Aluno.get_banca(None, aval_bancas)
    return nota_bancas

def media_orientador(projeto):
    alocacoes = Alocacao.objects.filter(projeto=projeto)
    if alocacoes:
        primeira = alocacoes.first()
        medias = primeira.get_media

        nota = 0
        peso = 0
        if ("peso_grupo_inter" in medias) and (medias["peso_grupo_inter"] is not None) and (medias["peso_grupo_inter"] > 0):
            nota += medias["nota_grupo_inter"]
            peso += medias["peso_grupo_inter"]
            
        if ("peso_grupo_final" in medias) and (medias["peso_grupo_final"] is not None) and (medias["peso_grupo_final"] > 0):
            nota += medias["nota_grupo_final"]
            peso += medias["peso_grupo_final"]
            
        if peso:
            return nota/peso
        return 0.0

    else:
        return 0.0
