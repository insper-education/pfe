#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Janeiro de 2024
"""

import logging
from datetime import date

from .models import Exame

from projetos.models import Documento, Evento, Avaliacao2, Observacao

from academica.support4 import get_banca_estudante

from estudantes.models import EstiloComunicacao

from users.models import Alocacao
from users.models import Aluno, UsuarioEstiloComunicacao


# Get an instance of a logger
logger = logging.getLogger("django")

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
    nota_banca_falconi, _, _ = get_banca_estudante(None, aval_banc_falconi)
    return nota_banca_falconi

def media_bancas(projeto):
    exames = Exame.objects.filter(titulo="Banca Final") | Exame.objects.filter(titulo="Banca Intermediária")
    aval_bancas = Avaliacao2.objects.filter(projeto=projeto, exame__in=exames)  # Bancas.
    nota_bancas, _, _ = get_banca_estudante(None, aval_bancas)
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



def get_respostas_estilos(usuario):
    
    valores = {
            "PR_Fav": 0,  # Pragmático - Escorre em Condições Favoráveis
            "PR_Str": 0,  # Pragmático - Escorre em Condições de Stress
            "S_Fav": 0,   # Afetivo - Escorre em Condições Favoráveis
            "S_Str": 0,   # Afetivo - Escorre em Condições de Stress
            "PN_Fav": 0,  # PN - Escorre em Condições Favoráveis
            "PN_Str": 0,  # PN - Escorre em Condições de Stress
            "I_Fav": 0,   # I - Escorre em Condições Favoráveis
            "I_Str": 0,   # I - Escorre em Condições de Stress
        }

    estilos = estilos = UsuarioEstiloComunicacao.objects.filter(usuario=usuario).exists()
    if not estilos:
        return None
    
    # PR_Fav = A1 + G1 + M1 + B3 + H3 + N3 + C4 + I4 + O4  # D5+D35+D65+D12+D42+D72+D18+D48+D78
    # PR_Str = D3 + J3 + P3 + E3 + K3 + Q3 + F2 + L2 + R2  # D22+D52+D82+D27+D57+D87+D31+D61+D91
    # S_Fav = A2 + G2 + M2 + B1 + H1 + N1 + O3 + I3 + C3  # D6+D36+D66+D10+D40+D70+D77+D47+D17
    # S_Str = D4 + J4 + P4 + E1 + K1 + Q1 + F4 + L4 + R4  # D23+D53+D83+D25+D55+D85+D33+D63+D93
    # PN_Fav = A3 + M3 + G3 + B2 + H3 + N2 + C2 + I2 + O2  # D7+D67+D37+D11+D41+D71+D16+D46+D76
    # PN_Str = D1 + J1 + P1 + E2 + K2 + Q2 + F1 + L1 + R1  # D20+D50+D80+D26+D56+D86+D30+D60+D90
    # I_Fav = A4 + G4 + M4 + B4 + H4 + N4 + C1 + I1 + O1  # D8+D38+D68+D13+D43+D73+D15+D45+D75
    # I_Str = D2 + J2 + P2 + E4 + K4 + Q4 + R3 + L3 + F3  # D21+D51+D81+D28+D58+D88+D92+D62+D32

    tabela = {
        "PR_Fav": ["A0", "G0", "M0", "B2", "H2", "N2", "C3", "I3", "O3"],
        "PR_Str": ["D2", "J2", "P2", "E2", "K2", "Q2", "F1", "L1", "R1"],
        "S_Fav": ["A1", "G1", "M1", "B0", "H0", "N0", "O2", "I2", "C2"],
        "S_Str": ["D3", "J3", "P3", "E0", "K0", "Q0", "F3", "L3", "R3"],
        "PN_Fav": ["A2", "M2", "G2", "B1", "H1", "N1", "C1", "I1", "O1"],
        "PN_Str": ["D0", "J0", "P0", "E1", "K1", "Q1", "F0", "L0", "R0"],
        "I_Fav": ["A3", "G3", "M3", "B3", "H3", "N3", "C0", "I0", "O0"],
        "I_Str": ["D1", "J1", "P1", "E3", "K3", "Q3", "R2", "L2", "F2"],
    }

    for estilo in EstiloComunicacao.objects.all():
        usuario_estilo = UsuarioEstiloComunicacao.objects.filter(usuario=usuario, estilo_comunicacao=estilo).last()
        if usuario_estilo and estilo.bloco:
            respostas = usuario_estilo.get_score_estilo()
            for k, v in tabela.items():
                for i in v:
                    if i[0] == estilo.bloco:
                        valores[k] += respostas[int(i[1])]

    return {
        "Pragmático Favorável": valores["PR_Fav"],
        "Pragmático Stress": valores["PR_Str"],
        "Afetivo Favorável": valores["S_Fav"],
        "Afetivo Stress": valores["S_Str"],
        "Racional Favorável": valores["PN_Fav"],
        "Racional Stress": valores["PN_Str"],
        "Reflexivo Favorável": valores["I_Fav"],
        "Reflexivo Stress": valores["I_Str"],
        "TOTAL Favorável": valores["PR_Fav"] + valores["S_Fav"] + valores["PN_Fav"] + valores["I_Fav"],
        "TOTAL Stress": valores["PR_Str"] + valores["S_Str"] + valores["PN_Str"] + valores["I_Str"],
    }
    
