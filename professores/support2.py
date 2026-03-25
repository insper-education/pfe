#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 8 de Janeiro de 2024
"""

from academica.support_notas import converte_letra


def _conceito_email(avaliacao):
    """Retorna conceito no mesmo padrão usado nas telas de avaliação."""
    if getattr(avaliacao, "na", False):
        return "N/A"

    if hasattr(avaliacao, "get_conceito"):
        try:
            conceito = avaliacao.get_conceito
            if callable(conceito):
                conceito = conceito()
            if conceito:
                return str(conceito)
        except Exception:
            pass

    if getattr(avaliacao, "nota", None) is not None:
        return converte_letra(avaliacao.nota)

    return "N/A"


def coleta_resumo_notas_bancas(avaliadores):
    """Organiza dados de avaliações para renderização em template (sem HTML por concatenação)."""
    obj_avaliados = {}
    agregacao_individual_alunos = {}
    avaliadores_detalhes = []

    for avaliador, objs in avaliadores.items():
        detalhe = {
            "avaliador": avaliador,
            "momento": objs.get("momento"),
            "conceitos_gerais": [],
            "conceitos_individuais": [],
            "observacoes_estudantes": objs.get("observacoes_estudantes"),
            "observacoes_orientador": objs.get("observacoes_orientador"),
        }

        for objetivo, conceito in objs.items():
            if objetivo in ["momento", "observacoes_estudantes", "observacoes_orientador", "avaliacoes_individuais"]:
                continue

            conceito_txt = _conceito_email(conceito)
            detalhe["conceitos_gerais"].append({
                "objetivo": objetivo,
                "conceito": conceito_txt,
                "nota": conceito.nota,
                "na": getattr(conceito, "na", False),
            })

            if conceito.nota is not None:
                if objetivo.titulo in obj_avaliados:
                    obj_avaliados[objetivo.titulo]["nota"] += conceito.nota
                    obj_avaliados[objetivo.titulo]["qtd"] += 1
                else:
                    obj_avaliados[objetivo.titulo] = {"nota": conceito.nota, "qtd": 1}

        if "avaliacoes_individuais" in objs and objs["avaliacoes_individuais"]:
            for alocacao, objetivos_ind in objs["avaliacoes_individuais"].items():
                aluno_info = {
                    "alocacao": alocacao,
                    "conceitos": [],
                }
                for objetivo_ind, conceito_ind in objetivos_ind.items():
                    conceito_txt = _conceito_email(conceito_ind)
                    aluno_info["conceitos"].append({
                        "objetivo": objetivo_ind,
                        "conceito": conceito_txt,
                        "nota": conceito_ind.nota,
                        "na": getattr(conceito_ind, "na", False),
                    })

                    if (not getattr(conceito_ind, "na", False)) and conceito_ind.nota is not None:
                        if alocacao not in agregacao_individual_alunos:
                            agregacao_individual_alunos[alocacao] = {"soma": 0, "qtd": 0}
                        agregacao_individual_alunos[alocacao]["soma"] += conceito_ind.nota
                        agregacao_individual_alunos[alocacao]["qtd"] += 1
                detalhe["conceitos_individuais"].append(aluno_info)

        avaliadores_detalhes.append(detalhe)

    medias_objetivos = []
    # Mantem compatibilidade com Decimal vindo do banco.
    soma_medias = 0
    for titulo, obj in obj_avaliados.items():
        if obj["qtd"] > 0:
            media = obj["nota"] / obj["qtd"]
            soma_medias += media
            medias_objetivos.append({
                "titulo": titulo,
                "media_numerica": media,
                "media_conceito": converte_letra(media),
            })

    media_final = None
    if medias_objetivos:
        media_final = soma_medias / len(medias_objetivos)

    medias_individuais_alunos = []
    for alocacao, dados in agregacao_individual_alunos.items():
        if dados["qtd"] > 0:
            media_aluno = dados["soma"] / dados["qtd"]
            medias_individuais_alunos.append({
                "alocacao": alocacao,
                "media_numerica": media_aluno,
                "media_conceito": converte_letra(media_aluno),
                "qtd_notas": dados["qtd"],
            })

    medias_individuais_alunos.sort(key=lambda x: x["alocacao"].aluno.user.get_full_name())

    return {
        "avaliadores": avaliadores_detalhes,
        "medias_objetivos": medias_objetivos,
        "media_final": media_final,
        "medias_individuais_alunos": medias_individuais_alunos,
    }


def calcula_media_notas_bancas(obj_avaliados):
    message = ""
    message += "<div style='color: red; border-width:3px; border-style:solid; border-color:#ff0000; display: inline-block; padding: 10px;'>"
    message += "<b> Média das avaliações: "
    message += "<ul>"
    medias = 0
    for txt, obj in obj_avaliados.items():
        if obj["qtd"] > 0.0:
            message += "<li>"
            message += txt
            message += ": "
            media = obj["nota"]/obj["qtd"]
            medias += media
            message += converte_letra(media)
            message += "</li>"
        else:
            message += "<li>N/A</li>"

    message += "</ul>"
    
    message += "&#10149; Nota Final Calculada = "
    if len(obj_avaliados):
        message += "<span>"
        message += "<b style='font-size: 1.16em;'>"
        message += "%.2f" % (medias/len(obj_avaliados))
        message += "</b><br>"
        message += "</span>"
    else:
        message += "<span>N/A</span>"

    message += "</b></div><br><br>"

    return message


def calcula_notas_bancas(avaliadores):
    obj_avaliados = {}
    
    message2 = "<table>"
    for avaliador, objs in avaliadores.items():
        
        message2 += "<tr><td>"
        message2 += "<strong>Avaliador"
        if avaliador.genero == "F":
            message2 += "a"
        message2 += ": </strong>"
        message2 += avaliador.get_full_name() + "<br>"

        if "momento" in objs:
            message2 += "<strong>Avaliado em: </strong>"
            message2 += objs["momento"].strftime('%d/%m/%Y às %H:%M') + "<br>"

        message2 += "<strong>Conceitos:</strong><br>"

        message2 += "<ul style='margin-top: 0px;'>"

        for objetivo, conceito in objs.items():
            if objetivo != "momento" and objetivo != "observacoes_estudantes" and objetivo != "observacoes_orientador" and objetivo != "avaliacoes_individuais":
                message2 += "<li>"
                message2 += objetivo.titulo
                message2 += " : "
                if conceito.nota is not None:
                    message2 += converte_letra(conceito.nota)                
                    message2 += "</li>"
                    if objetivo.titulo in obj_avaliados:
                        obj_avaliados[objetivo.titulo]["nota"] += conceito.nota
                        obj_avaliados[objetivo.titulo]["qtd"] += 1
                    else:
                        obj_avaliados[objetivo.titulo] = {}
                        obj_avaliados[objetivo.titulo]["nota"] = conceito.nota
                        obj_avaliados[objetivo.titulo]["qtd"] = 1
                else:
                    message2 += "N/A</li>"

        if "observacoes_estudantes" in objs and objs["observacoes_estudantes"]:
            message2 += "<li>Observações Estudantes: " + objs["observacoes_estudantes"] + "</li>"
        if "observacoes_orientador" in objs and objs["observacoes_orientador"]:
            message2 += "<li>Observações Orientador: " + objs["observacoes_orientador"] + "</li>"
        
        message2 += "</ul>"

        if "avaliacoes_individuais" in objs and objs["avaliacoes_individuais"]:
            message2 += "<strong>Conceitos Individuais (BI/BF):</strong><br>"
            for alocacao, objetivos_ind in objs["avaliacoes_individuais"].items():
                message2 += "<div style='margin: 6px 0 8px 0; border:1px solid #ddd; padding:6px 8px;'>"
                message2 += "<strong>Estudante:</strong> " + alocacao.aluno.user.get_full_name()
                message2 += "<ul style='margin-top: 4px;'>"
                for objetivo_ind, conceito_ind in objetivos_ind.items():
                    message2 += "<li>"
                    message2 += objetivo_ind.titulo
                    message2 += " : "
                    if conceito_ind.nota is not None:
                        message2 += converte_letra(conceito_ind.nota)
                    else:
                        message2 += "N/A"
                    message2 += "</li>"
                message2 += "</ul>"
                message2 += "</div>"

        message2 += "</td></tr>"


    message2 += "</td></tr>"
    message2 += "</table>"

    return message2, obj_avaliados

