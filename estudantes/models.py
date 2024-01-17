from django.db import models

import datetime

class Relato(models.Model):
    """Avaliações realizadas durante o projeto."""

    momento = models.DateTimeField("Momento", default=datetime.datetime.now, blank=True,
                                   help_text='Data e hora do relato') # hora ordena para dia

    # Para Alocações dos estudantes (caso um aluno reprove ele teria duas alocações)
    alocacao = models.ForeignKey('users.Alocacao', null=True, blank=True,
                                 on_delete=models.SET_NULL,
                                 related_name='projeto_alocado_relato',
                                 help_text='relacao de alocação entre projeto e estudante')

    texto = models.TextField("Texto", max_length=2100, null=True, blank=True,
                                   help_text='Texto do relato')

    avaliacao = models.DecimalField("Avaliação", default=-1, max_digits=2, decimal_places=0,
                                                 help_text='nota obtida na avaliação do orientador')

    def __str__(self):
        return str(self.alocacao) + " (" + str(self.momento) + ") "

    @classmethod
    def create(cls):
        """Cria um objeto (entrada) em Relato."""
        relato = cls()
        return relato

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
                                    related_name='projeto_alocado_pares_de',
                                    help_text='relacao de uma aluno para com outro (DE)')

    # Para Alocações dos estudantes (caso um aluno reprove ele teria duas alocações)
    alocacao_para = models.ForeignKey("users.Alocacao", null=True, blank=True,
                                      on_delete=models.SET_NULL,
                                      related_name='projeto_alocado_pares_para',
                                      help_text='relacao de uma aluno para com outro (PARA)')

    TIPO_TIPO = (
        (0, 'intermediaria'),
        (1, 'final'),
    )
    tipo = models.PositiveSmallIntegerField(choices=TIPO_TIPO,
                                               null=True, blank=True,
                                               help_text='Define o tipo de avaliação de pares')

    aprecia = models.TextField("Aprecia", max_length=1000, null=True, blank=True,
                                   help_text='O que você aprecia no colega ')

    atrapalhando = models.TextField("Atrapalhando", max_length=1000, null=True, blank=True,
                                   help_text='O que você ve o colega atrapalhando')
    
    mudar = models.TextField("Mudar", max_length=1000, null=True, blank=True,
                                   help_text='O que o colega pode mudar')
    
    TIPO_ENTREGA = (
        (0, 'Entregou muito abaixo de esperado, colocando a entrega em risco e obrigando outro(s) membro(s) a mudarem planejamentos pessoais para garanti-la.'),
        (1, 'Entregou abaixo do esperado.'),
        (2, 'Entregou precisamente o esperado.'),
        (3, 'Entregou acima do esperado.'),
        (4, 'Entregou muito acima do esperado, mudando planejamentos pessoais para garantir uma entrega que estava em risco.'),
    )
    entrega = models.PositiveSmallIntegerField(choices=TIPO_ENTREGA,
                                               null=True, blank=True,
                                               help_text='Define o tipo de entrega')

    TIPO_INICIATIVA = (
        (0, 'Mesmo quando lembrado, não cumpriu as tarefas designadas.'),
        (1, 'Precisou ser lembrado, mas cumpriu as tarefas designadas.'),
        (2, 'Autonomamente, cumpriu as tarefas designadas, nem mais nem menos.'),
        (3, 'Além de cumprir as tarefas designadas, ajudou outros(s) membro(s) que estavam tendo dificuldades.'),
        (4, 'Monopolizou parte das tarefas, assumindo tarefas de outro(s) membro(s) mesmo quando não havia evidência de dificuldades.'),
    )
    iniciativa = models.PositiveSmallIntegerField(choices=TIPO_INICIATIVA,
                                               null=True, blank=True,
                                               help_text='Define o tipo de entrega')

    TIPO_COMUNICACAO = (
        (0, 'Teve dificuldades, nunca as comunicou e ao final elas impediram a entrega.'),
        (1, 'Teve dificuldades e nunca as comunicou, mas pelo menos não impediram a entrega.'),
        (2, 'Aparentemente não teve dificuldades, mas nunca reportou nada.'),
        (3, 'Comunicou dificuldades. Independente da entrega ter sido feita ou não, a equipe não foi surpreendida.'),
        (4, 'Apesar de não ter dificuldades, estava sempre reportando como estava indo.'),
    )
    comunicacao = models.PositiveSmallIntegerField(choices=TIPO_COMUNICACAO,
                                               null=True, blank=True,
                                               help_text='Define o tipo de entrega')

    def __str__(self):
        return str(self.alocacao_de) + " -> " + str(self.alocacao_para)

    @classmethod
    def create(cls):
        """Cria um objeto (entrada) em Pares."""
        pares = cls()
        return pares

    class Meta:
        verbose_name = 'Avaliação de Pares'
        verbose_name_plural = 'Avaliações de Pares'