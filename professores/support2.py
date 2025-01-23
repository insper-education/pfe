#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 8 de Janeiro de 2024
"""

from academica.support_notas import converte_letra, arredonda_conceitos


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
            medias += arredonda_conceitos(media)
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
            if objetivo != "momento" and objetivo != "observacoes_estudantes" and objetivo != "observacoes_orientador":
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
        message2 += "</td></tr>"


    message2 += "</td></tr>"
    message2 += "</table>"

    return message2, obj_avaliados

