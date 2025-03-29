#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 28 de Março de 2025
"""

from django import template
register = template.Library()


@register.filter
def tipo_usuario(objeto, lingua):
    """ Retorna o tipo de usuário, por língua. """
    
    if lingua == "pt":
        """Retorna o tipo de usuário."""
        if objeto.tipo_de_usuario == 1:
            return "Estudante"
        elif objeto.tipo_de_usuario == 2:
            return "Professor"
        elif objeto.tipo_de_usuario == 3:
            return "Parceiro"
        elif objeto.tipo_de_usuario == 4:
            return "Administrador"
        else:
            return "Desconhecido"
        
    elif lingua == "en":
        """Retorna o tipo de usuário em inglês."""
        if objeto.tipo_de_usuario == 1:
            return "Student"
        elif objeto.tipo_de_usuario == 2:
            return "Professor"
        elif objeto.tipo_de_usuario == 3:
            return "Partner"
        elif objeto.tipo_de_usuario == 4:
            return "Administrator"
        else:
            return "Unknown"
    
    return "ERRO"