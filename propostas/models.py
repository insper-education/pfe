#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 27 de Novembro de 2024
"""

from django.db import models


class PerguntasRespostas(models.Model):
    """Modelo de Perguntas e Respostas."""

    proposta = models.ForeignKey("projetos.Proposta", null=True, blank=True,   
                                    on_delete=models.SET_NULL,
                                    help_text="Proposta relacionada a pergunta")

    pergunta = models.TextField("Pergunta", max_length=3000, null=True, blank=True,
                                help_text="Pergunta de estudante para uma proposta")
    resposta = models.TextField("Resposta", max_length=3000, null=True, blank=True,
                                help_text="Resposta para uma proposta")
    
    data_pergunta = models.DateTimeField("Data", auto_now_add=True, help_text="Data da pergunta")
    data_resposta = models.DateTimeField("Data", auto_now_add=True, help_text="Data da resposta")

    quem_perguntou = models.ForeignKey("users.PFEUser", null=True, blank=True,
                                       on_delete=models.SET_NULL, related_name="quem_perguntou",
                                       help_text="Quem fez a pergunta")
    quem_respondeu = models.ForeignKey("users.PFEUser", null=True, blank=True,
                                        on_delete=models.SET_NULL, related_name="quem_respondeu",
                                        help_text="Quem respondeu a pergunta")
    
    def __str__(self):
        return self.pergunta
