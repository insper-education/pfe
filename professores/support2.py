#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 8 de Janeiro de 2024
"""

def converte_conceitos(nota):
    if( nota >= 9.5 ): return ("A+")
    if( nota >= 9.0 ): return ("A")
    if( nota >= 8.0 ): return ("B+")
    if( nota >= 7.0 ): return ("B")
    if( nota >= 6.0 ): return ("C+")
    if( nota >= 5.0 ): return ("C")
    if( nota >= 4.0 ): return ("D+")
    if( nota >= 3.0 ): return ("D")
    if( nota >= 2.0 ): return ("D-")
    if( nota >= 0.0 ): return ("I")
    return "inválida"

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