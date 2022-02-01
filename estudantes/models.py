from django.db import models

import datetime

class Relato(models.Model):
    """Avaliações realizadas durante o projeto."""

    momento = models.DateTimeField(default=datetime.datetime.now, blank=True,
                                   help_text='Data e hora do relato') # hora ordena para dia

    # Para Alocações dos estudantes (caso um aluno reprove ele teria duas alocações)
    alocacao = models.ForeignKey('users.Alocacao', null=True, blank=True,
                                 on_delete=models.SET_NULL,
                                 related_name='projeto_alocado_relato',
                                 help_text='relacao de alocação entre projeto e estudante')

    texto = models.TextField("Texto", max_length=1000, null=True, blank=True,
                                   help_text='Texto do relato')


    def __str__(self):
        return str(self.alocacao) + " (" + str(self.momento) + ") "

    @classmethod
    def create(cls):
        """Cria um objeto (entrada) em Relato."""
        relato = cls()
        return relato

    class Meta:
        verbose_name = 'Relato'
        verbose_name_plural = 'Relatos'
        ordering = ['momento', 'alocacao']
