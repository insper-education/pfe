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



class FuncionalidadeGrupo(models.Model):
    FAIXA_ESCOLHAS = [
        (1, '1'),
        (2, '2'),
        (3, '3'),
    ]

    question_1 = models.IntegerField("Os membros da equipe são veementes e espontâneos quando discutem questões de interesse comum?", choices=FAIXA_ESCOLHAS)
    question_2 = models.IntegerField("Os membros da equipe criticam as falhas ou os comportamentos contraproducentes uns dos outros?", choices=FAIXA_ESCOLHAS)
    question_3 = models.IntegerField("Os membros da equipe sabem exatamente em que seus colegas estão trabalhando e como eles contribuem para o bem coletivo?", choices=FAIXA_ESCOLHAS)
    question_4 = models.IntegerField("Os membros da equipe pedem desculpas sinceras uns aos outros quando dizem ou fazem algo inapropriado ou que possa prejudicar a equipe?", choices=FAIXA_ESCOLHAS)
    question_5 = models.IntegerField("Os membros da equipe fazem sacrifícios (em termos, por exemplo, de orçamento, território, número de pessoal) de boa vontade em seus departamentos ou áreas de conhecimento, pelo bem da equipe?", choices=FAIXA_ESCOLHAS)
    question_6 = models.IntegerField("Os membros da equipe admitem abertamente suas fraquezas e seus erros?", choices=FAIXA_ESCOLHAS)
    question_7 = models.IntegerField("As reuniões de equipe são instigantes e não tediosas?", choices=FAIXA_ESCOLHAS)
    question_8 = models.IntegerField("Os membros da equipe saem das reuniões confiantes em que seus colegas estão totalmente comprometidos com as decisões acordadas, ainda que tenha havido uma discordância inicial?", choices=FAIXA_ESCOLHAS)
    question_9 = models.IntegerField("O ânimo da equipe é afetado de forma significativa quando algum objetivo coletivo não é alcançado?", choices=FAIXA_ESCOLHAS)
    question_10 = models.IntegerField("Durante as reuniões de equipe, as questões mais importantes e difíceis são colocadas em pauta para serem resolvidas?", choices=FAIXA_ESCOLHAS)
    question_11 = models.IntegerField("Os membros da equipe se preocupam em não decepcionar os colegas?", choices=FAIXA_ESCOLHAS)
    question_12 = models.IntegerField("Os membros da equipe conhecem a vida pessoal uns dos outros e se sentem à vontade falando sobre esse tema?", choices=FAIXA_ESCOLHAS)
    question_13 = models.IntegerField("Os membros da equipe terminam as discussões com resoluções claras e específicas e com tarefas a realizar?", choices=FAIXA_ESCOLHAS)
    question_14 = models.IntegerField("Os membros da equipe desafiam-se uns aos outros em relação a seus planos e abordagens?", choices=FAIXA_ESCOLHAS)
    question_15 = models.IntegerField("Os membros da equipe demoram a cobrar o crédito das próprias contribuições, mas são rápidos em apontar as contribuições dos colegas?", choices=FAIXA_ESCOLHAS)

    def __str__(self):
        return f"Funcionalidade de Grupo {self.id}"

    class Meta:
        verbose_name = "Funcionalidade de Grupo"
        verbose_name_plural = "Funcionalidades de Grupo"
