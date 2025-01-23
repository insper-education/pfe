#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 23 de Janeiro de 2025
"""

def converte_conceito(conceito):
    """Converte de Letra para Número."""
    if conceito == "A+":
        return 10
    elif conceito in ("A", "A "):
        return 9
    elif conceito == "B+":
        return 8
    elif conceito in ("B", "B "):
        return 7
    elif conceito == "C+":
        return 6
    elif conceito in ("C", "C "):
        return 5
    elif conceito in ("D+", "D+ "):
        return 4
    elif conceito in ("D", "D "):
        return 3
    elif conceito in ("D-", "D- "):
        return 2
    return 0


def converte_letra(nota, mais="+", espaco=""):
    """Converte de Número para Letra."""
    if nota is None:
        return None
    if nota > 9.99:  #if nota > 9.5:
        return "A"+mais
    elif nota >= 9: #elif nota >= 8.5:
        return "A"+espaco
    elif nota >= 8:  #elif nota >= 7.5:
        return "B"+mais
    elif nota >= 7:  #elif nota >= 6.5:
        return "B"+espaco
    elif nota >= 6:  #elif nota >= 5.5:
        return "C"+mais
    elif nota >= 5:  #elif nota >= 4.5:
        return "C"+espaco
    elif nota >= 4:  #elif nota >= 3.5:
        return "D"+mais
    elif nota >= 3:  #elif nota >= 2.5:
        return "D"+espaco
    elif nota >= 2:  #elif nota >= 1.5:
        return "D"+"-"
    return "I"+espaco

def arredonda_conceitos(nota):
    if( nota >= 9.5 ): return 10
    if( nota >= 8.5 ): return 9
    if( nota >= 7.5 ): return 8
    if( nota >= 6.5 ): return 7
    if( nota >= 5.5 ): return 6
    if( nota >= 4.5 ): return 5
    if( nota >= 3.5 ): return 4
    if( nota >= 2.5 ): return 3
    if( nota >= 1.5 ): return 2
    return 0
