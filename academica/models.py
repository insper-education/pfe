#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 4 de Novembro de 2023
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from administracao.models import TipoEvento

from projetos.tipos import TIPO_EVENTO

class Exame(models.Model):
    """Exames que são realizados durante o semestre."""

    titulo = models.TextField("Título", max_length=128, null=True, blank=True, unique=True,
                              help_text="Título do Exame")
    
    titulo_en = models.TextField("Título (Inglês)", max_length=128, null=True, blank=True,
                                 help_text="Título do Exame em Inglês")
    
    sigla = models.TextField("Sigla", max_length=3, null=True, blank=True, unique=True,
                             help_text="Sigla do Exame")

    grupo = models.BooleanField("Grupo", default=False,
                                help_text="Caso Verdadeiro é em Grupo, se Falso é individual")
    
    banca = models.BooleanField("Banca", default=False,
                                help_text="Caso Verdadeiro é um exame em formato de Banca")
    
    PERIODOS_RUBRICAS = (
        (0, "Não Aplicável"),
        (1, "Intermediário"),
        (2, "Final"),
    )
    periodo_para_rubricas = models.PositiveSmallIntegerField(choices=PERIODOS_RUBRICAS, default=0)
    
    comentario = models.TextField(max_length=256, null=True, blank=True,
                                  help_text="qualquer observação relevante")
    
    cor = models.TextField("Cor", max_length=6, null=True, blank=True, default="777777",
                           help_text="Cor do Exame em hexadecimal")
    
    def __str__(self):
        return str(self.titulo) 

    @classmethod
    def create(cls, titulo):
        """Cria um objeto (entrada) em Exame."""
        exame = cls(titulo=titulo)
        return exame
    
    class Meta:
        verbose_name = "Exame"
        verbose_name_plural = "Exames"


class Composicao(models.Model):
    """Composição para as Avaliações, Eventos e Entregáveis."""

    exame = models.ForeignKey("academica.Exame", null=True, blank=True, on_delete=models.SET_NULL,
                                 help_text="Tipo de avaliação")

    tipo_documento = models.ForeignKey("documentos.TipoDocumento", null=True, blank=True, on_delete=models.SET_NULL,
                                help_text="Tipo de documento")

    evento = models.PositiveSmallIntegerField(choices=[subl[:2] for subl in TIPO_EVENTO],
                                                      null=True, blank=True,
                                                      help_text="Tipo do evento esperado para uma entrega")
    
    tipo_evento = models.ForeignKey("administracao.TipoEvento", null=True, blank=True, on_delete=models.SET_NULL,
                                      help_text="Tipo de evento")
    
    entregavel = models.BooleanField(default=True, help_text="Entregável")

    pesos = models.ManyToManyField("projetos.ObjetivosDeAprendizagem", through="Peso",
                                    help_text="Pesos dos Objetivos de Aprendizado por Avaliação")

    data_inicial = models.DateField("Data Inicial", null=True, blank=True,
                                    help_text="Data Inicial de Uso")

    data_final = models.DateField("Data Final", null=True, blank=True,
                                  help_text="Data Final de Uso")

    orientacoes = models.TextField(max_length=4096, null=True, blank=True,
                                   help_text="orientações para a avaliação em português")
    
    orientacoes_en = models.TextField(max_length=4096, null=True, blank=True,
                                      help_text="orientações para a avaliação em inglês")

    duracao_banca = models.PositiveSmallIntegerField("Duração da Banca", default=0,
                                                     help_text="Duração da Banca em minutos (se for uma banca)")


    def __str__(self):
        texto = str(self.exame) + "  [ "
        if self.data_inicial:
            texto += str(self.data_inicial)
        texto += " -> "
        if self.data_final:
            texto += str(self.data_final)
        else:
            texto += "hoje"
        texto += " ]"
        return texto

    @classmethod
    def create(cls, organizacao):
        """Cria um objeto (entrada) em Composicao."""
        anotacao = cls(organizacao=organizacao)
        return anotacao

    def get_composicoes(ano, semestre):
        """Filtra composições para um semestre."""
        composicoes = Composicao.objects.all()\
            .exclude(data_final__year__lt=ano)\
            .exclude(data_inicial__year__gt=ano)
        if semestre == 1:
            composicoes = composicoes.exclude(data_inicial__year=ano, data_inicial__month__gt=6)
        else:
            composicoes = composicoes.exclude(data_final__year=ano, data_final__month__lt=8)
        return composicoes

    class Meta:
        verbose_name = "Composição"
        verbose_name_plural = "Composições"
        ordering = [ "exame", "data_inicial",]


class Peso(models.Model):
    """Relação entre avaliação e entrega."""

    composicao = models.ForeignKey(Composicao, null=True, blank=True,
                                   on_delete=models.SET_NULL)

    objetivo = models.ForeignKey("projetos.ObjetivosDeAprendizagem", null=True, blank=True,
                                 on_delete=models.SET_NULL)

    peso = models.FloatField("Peso", validators=[MinValueValidator(0), MaxValueValidator(100)], null=True, blank=True,
                             help_text='Pesa da avaliação na média em % (varia de 0 a 100)')
    class Meta:
        """Meta para Peso."""
        verbose_name = "Peso"
        verbose_name_plural = "Pesos"
        permissions = (("altera_professor", "Professor altera valores"), )

    def __str__(self):
        """Retorno padrão textual do objeto."""
        mensagem = ""
        if self.composicao:
            mensagem += str(self.composicao.exame)
        mensagem += " >>> "
        if self.objetivo:
            mensagem += str(self.objetivo)
        return mensagem


class CodigoColuna(models.Model):
    """Código da Coluna de nota do Blackboard."""

    exame = models.ForeignKey("academica.Exame", null=True, blank=True, on_delete=models.SET_NULL,
                                 help_text="Tipo de avaliação")

    ano = models.PositiveIntegerField("Ano",
                                      validators=[MinValueValidator(2018), MaxValueValidator(3018)],
                                      help_text="Ano das avaliações")

    semestre = models.PositiveIntegerField("Semestre",
                                           validators=[MinValueValidator(1), MaxValueValidator(2)],
                                           help_text="Semestre das avaliações")
    
    coluna = models.TextField("Coluna", max_length=8, null=True, blank=True,
                                help_text="Coluna de Notas no Blackboard")

class ExibeNota(models.Model):
    """Código da Coluna de nota do Blackboard."""

    exame = models.ForeignKey("academica.Exame", null=True, blank=True, on_delete=models.SET_NULL,
                                 help_text="Tipo de avaliação")

    ano = models.PositiveIntegerField("Ano",
                                      validators=[MinValueValidator(2018), MaxValueValidator(3018)],
                                      help_text="Ano das avaliações")

    semestre = models.PositiveIntegerField("Semestre",
                                           validators=[MinValueValidator(1), MaxValueValidator(2)],
                                           help_text="Semestre das avaliações")
    
    exibe = models.BooleanField("Exibe", default=True,
                             help_text="Exibe as notas para os estudantes")
