#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Dezembro de 2020
"""

from django.db import models

import datetime

class Relato(models.Model):
    """Avaliações realizadas durante o projeto."""

    momento = models.DateTimeField("Momento", default=datetime.datetime.now, blank=True,
                                   help_text="Data e hora do relato")  # hora ordena para dia

    # Para Alocações dos estudantes (caso um aluno reprove ele teria duas alocações)
    alocacao = models.ForeignKey("users.Alocacao", null=True, blank=True,
                                 on_delete=models.SET_NULL,
                                 related_name="projeto_alocado_relato",
                                 help_text="relacao de alocação entre projeto e estudante")

    texto = models.TextField("Texto", max_length=2100, null=True, blank=True,
                                   help_text="Texto do relato")
    
    momento_avaliacao = models.DateTimeField("Momento da Avaliação", null=True, blank=True,
                                   help_text="Data e hora da avaliação do relato")

    avaliacao = models.DecimalField("Avaliação", default=-1, max_digits=2, decimal_places=0,
                                                 help_text="nota obtida na avaliação do orientador")

    feedback = models.TextField("Feedback", max_length=2100, null=True, blank=True,
                                   help_text="Possível feedback do orientador para os estudantes")

    def __str__(self):
        return str(self.alocacao) + " (" + str(self.momento) + ") "
    
    class Meta:
        verbose_name = "Relato"
        verbose_name_plural = "Relatos"


class Pares(models.Model):
    """Avaliações de Pares."""

    momento = models.DateTimeField("Momento", default=datetime.datetime.now, blank=True,
                                   help_text='Data e hora do relato') # hora ordena para dia

    # Para Alocações dos estudantes (caso um aluno reprove ele teria duas alocações)
    alocacao_de = models.ForeignKey("users.Alocacao", null=True, blank=True,
                                    on_delete=models.SET_NULL,
                                    related_name="projeto_alocado_pares_de",
                                    help_text="relacao de uma aluno para com outro (DE)")

    # Para Alocações dos estudantes (caso um aluno reprove ele teria duas alocações)
    alocacao_para = models.ForeignKey("users.Alocacao", null=True, blank=True,
                                      on_delete=models.SET_NULL,
                                      related_name="projeto_alocado_pares_para",
                                      help_text="relacao de uma aluno para com outro (PARA)")

    TIPO_TIPO = (
        (0, "intermediaria"),
        (1, "final"),
    )
    tipo = models.PositiveSmallIntegerField(choices=TIPO_TIPO,
                                               null=True, blank=True,
                                               help_text="Define o tipo de avaliação de pares")

    aprecia = models.TextField("Aprecia", max_length=1000, null=True, blank=True,
                                   help_text="O que você aprecia no colega ")

    atrapalhando = models.TextField("Atrapalhando", max_length=1000, null=True, blank=True,
                                   help_text="O que você ve o colega atrapalhando")
    
    mudar = models.TextField("Mudar", max_length=1000, null=True, blank=True,
                                   help_text="O que o colega pode mudar")
    
    TIPO_ENTREGA = (
        (0, "Entregou muito abaixo de esperado, colocando a entrega em risco e obrigando outro(s) membro(s) a mudarem planejamentos pessoais para garanti-la.", "Delivered well below expectations, putting the delivery at risk and forcing other member(s) to change personal plans to guarantee it."),
        (1, "Entregou abaixo do esperado.",  "Delivered below expectations."),
        (2, "Entregou precisamente o esperado.", "Delivered exactly what was expected."),
        (3, "Entregou acima do esperado.", "Delivered above expectations."),
        (4, "Entregou muito acima do esperado, mudando planejamentos pessoais para garantir uma entrega que estava em risco.", "Delivered well above expectations, changing personal plans to guarantee a delivery that was at risk."),
    )
    entrega = models.PositiveSmallIntegerField(choices=[subl[:2] for subl in TIPO_ENTREGA],
                                               null=True, blank=True,
                                               help_text="Define o tipo de entrega")

    TIPO_INICIATIVA = (
        (0, "Mesmo quando lembrado, não cumpriu as tarefas designadas.", "Even when reminded, did not fulfill the assigned tasks."),
        (1, "Precisou ser lembrado, mas cumpriu as tarefas designadas.", "Needed to be reminded, but fulfilled the assigned tasks."),
        (2, "Autonomamente, cumpriu as tarefas designadas, nem mais nem menos.", "Autonomously, fulfilled the assigned tasks, neither more nor less."),
        (3, "Além de cumprir as tarefas designadas, ajudou outros(s) membro(s) que estavam tendo dificuldades.", "In addition to fulfilling the assigned tasks, helped other member(s) who were having difficulties."),
        (4, "Monopolizou parte das tarefas, assumindo tarefas de outro(s) membro(s) mesmo quando não havia evidência de dificuldades.", "Monopolized part of the tasks, assuming tasks of other member(s) even when there was no evidence of difficulties."),
    )
    iniciativa = models.PositiveSmallIntegerField(choices=[subl[:2] for subl in TIPO_INICIATIVA],
                                                  null=True, blank=True,
                                                  help_text="Define o tipo de entrega")

    TIPO_COMUNICACAO = (
        (0, "Teve dificuldades, nunca as comunicou e ao final elas impediram a entrega.", "Had difficulties, never communicated them and in the end they prevented the delivery."),
        (1, "Teve dificuldades e nunca as comunicou, mas pelo menos não impediram a entrega.", "Had difficulties and never communicated them, but at least it did not prevent the delivery."),
        (2, "Aparentemente não teve dificuldades, mas nunca reportou nada.", "Apparently had no difficulties, but never reported anything."),
        (3, "Comunicou dificuldades. Independente da entrega ter sido feita ou não, a equipe não foi surpreendida.", "Communicated difficulties. Regardless of whether the delivery was made or not, the team was not surprised."),
        (4, "Apesar de não ter dificuldades, estava sempre reportando como estava indo.", "Despite having no difficulties, was always reporting how it was going."),
    )
    comunicacao = models.PositiveSmallIntegerField(choices=[subl[:2] for subl in TIPO_COMUNICACAO],
                                               null=True, blank=True,
                                               help_text="Define o tipo de entrega")

    def __str__(self):
        return str(self.alocacao_de) + " -> " + str(self.alocacao_para)

    class Meta:
        verbose_name = "Avaliação de Pares"
        verbose_name_plural = "Avaliações de Pares"


class EstiloComunicacao(models.Model):
    """Estilos de Comunicação."""

    bloco = models.CharField(max_length=1, verbose_name="Código do Bloco", null=True, blank=True)
    
    questao = models.TextField("Questão", max_length=256, null=True, blank=True,
                                   help_text="Questão a ser respondida")
    
    resposta1 = models.TextField("Resposta 1", max_length=256, null=True, blank=True)
    resposta2 = models.TextField("Resposta 2", max_length=256, null=True, blank=True)
    resposta3 = models.TextField("Resposta 3", max_length=256, null=True, blank=True)
    resposta4 = models.TextField("Resposta 4", max_length=256, null=True, blank=True)

    def __str__(self):
        return self.bloco + " - " + self.questao
    
    class Meta:
        verbose_name = "Estilo de Comunicação"
        verbose_name_plural = "Estilos de Comunicação"
