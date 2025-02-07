#!/usr/bin/env python
#pylint: disable=unused-argument
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Maio de 2019
"""

import re
import logging
from hashids import Hashids
from urllib.parse import quote
from functools import partial

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from projetos.support import get_upload_path

# Get an instance of a logger
logger = logging.getLogger("django")

class PFEUser(AbstractUser):
    """Classe base para todos os usuários."""

    # Atualizar para AbstractBaseUser que permite colocar mais caracteres em
    # username
    # first_name
    # last_name
    # Tambem tem: get_full_name()
    # email
    # is_active
    # add additional fields in here
    TIPO_DE_USUARIO_CHOICES = (
        (1, "estudante"),
        (2, "professor"),
        (3, "parceiro"),
        (4, "administrador"),
    )
    tipo_de_usuario = \
        models.PositiveSmallIntegerField(choices=TIPO_DE_USUARIO_CHOICES, default=1,
                                         help_text="cada usuário tem um perfil único")

    telefone = models.CharField(max_length=26, null=True, blank=True,
                                help_text="Telefone Fixo")
    celular = models.CharField(max_length=26, null=True, blank=True,
                               help_text="Telefone Celular")
    instant_messaging = models.CharField(max_length=32, null=True, blank=True,
                             help_text="Identificação IM, como Skype, Zoom, Teams, etc")

    linkedin = models.URLField("LinkedIn", max_length=256, null=True, blank=True,
                               help_text="LinkedIn do usuário")

    membro_comite = \
        models.BooleanField("Membro do Comitê", default=False, help_text="caso membro do comitê")

    GENERO_CHOICES = (
        ('X', "Não Informado"),
        ('M', "Masculino"),
        ('F', "Feminino"),
    )
    genero = models.CharField("Gênero", max_length=1, choices=GENERO_CHOICES, default='X',
                              help_text="sexo do usuário")

    TIPO_LINGUA = (
        (1, "português"),
        (2, "inglês"),
    )
    tipo_lingua = models.PositiveSmallIntegerField("Língua", choices=TIPO_LINGUA, default=1,
                                                   help_text="língua usada para comunicação")

    observacoes = models.TextField("Observações", max_length=500, null=True, blank=True,
                                   help_text="Observações")

    pronome_tratamento = models.CharField("Pronome de Tratamento", max_length=8, null=True, blank=True)

    nome_social = models.CharField(max_length=150, null=True, blank=True,
                                   help_text="Na prática o nome que a pessoa é (ou gostaria de ser) chamada")
    
    funcionalidade_grupo = models.ForeignKey("estudantes.FuncionalidadeGrupo", null=True, blank=True, on_delete=models.SET_NULL,
                               help_text="Resultados da Funcionalidade de Grupo")

    class Meta:
        """Classe Meta."""
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"
        ordering = [ "first_name", "last_name"]
        
    # Estou sobreescrevendo a função get_full_name para que ela retorne o pronome de tratamento e nome social
    def get_full_name(self):
        texto = ""
        if self.pronome_tratamento:
            texto += self.pronome_tratamento + ' '
        if self.nome_social:
            texto += self.nome_social
        else:
            texto += self.first_name + ' ' + self.last_name
        return texto.strip()

    def get_celular(self):
        """Retorna o celular do usuário."""
        if self.celular:
            # Se o celular for um número de telefone, retorna ele formatado
            celular =   re.sub(r'[^\d\+]', '', self.celular)
            if celular[0] != '+':
                if len(celular) == 11:
                    celular = "+55 (" + celular[:2] + ") " + celular[2:7] + "-" + celular[7:]
                elif len(celular) == 9:
                    celular = "+55 (11) " + celular[:5] + "-" + celular[5:]
            return celular
        return None
    
    def estud(self):
        """Retorna se é estudante."""
        return self.tipo_de_usuario == 1

    @property
    def eh_estud(self):
        """Retorna se é estudante."""
        return self.tipo_de_usuario == 1

    def prof(self):
        """Retorna se é professor (ou Administrador)."""
        return self.tipo_de_usuario == 2
    
    @property
    def eh_prof(self):
        """Retorna se é professor (ou Administrador)."""
        return self.tipo_de_usuario == 2

    def prof_a(self):
        """Retorna se é professor (ou Administrador)."""
        return self.tipo_de_usuario == 2 or self.tipo_de_usuario == 4
    
    @property
    def eh_prof_a(self):
        """Retorna se é professor (ou Administrador)."""
        return self.tipo_de_usuario == 2 or self.tipo_de_usuario == 4
        
    def parc(self):
        """Retorna se é parceiro."""
        return self.tipo_de_usuario == 3
    
    @property
    def eh_parc(self):
        """Retorna se é parceiro."""
        return self.tipo_de_usuario == 3
    
    def admin(self):
        """Retorna se é administrador."""
        return self.tipo_de_usuario == 4
    
    @property
    def eh_admin(self):
        """Retorna se é administrador."""
        return self.tipo_de_usuario == 4

    def __str__(self):
        """Retorno padrão textual do objeto."""
        texto = self.get_full_name()
        if self.tipo_de_usuario == 1 and hasattr(self, "aluno"):  # (1, "aluno"),
            texto += " (estudante"
            if self.aluno.anoPFE and self.aluno.semestrePFE:
                texto += " : " + str(self.aluno.anoPFE) + "." + str(self.aluno.semestrePFE)
        elif self.tipo_de_usuario == 2 and hasattr(self, "professor"):  # (2, "professor"),
            texto += " (professor"
            if self.professor.dedicacao:
                texto += " : " + self.professor.dedicacao
        elif self.tipo_de_usuario == 3 and hasattr(self, "parceiro"):  # (3, "parceiro"),
            texto += " (parceiro"
            if self.parceiro.organizacao and self.parceiro.organizacao.sigla:
                texto += " : " + self.parceiro.organizacao.sigla
        elif self.tipo_de_usuario == 4:  # (4, "administrador"),
            texto += " (professor : TI"

        texto += ")"
        return texto

    @property
    def hashid(self):
        """Recuper o hash id do usuário."""
        hashids = Hashids(salt=settings.SALT, min_length=8)
        hid = hashids.encode(self.id)
        return hid

class Professor(models.Model):
    """Classe de usuários com estatus de Professor."""

    user = models.OneToOneField(PFEUser, related_name="professor", on_delete=models.CASCADE)

    TIPO_DEDICACAO = (
        ("TI", "Tempo Integral"),
        ("TP", "Tempo Parcial"),
        ("V", "Visitante"),
        ("E", "Externo"),
        ("O", "Outro"),
    )

    dedicacao = models.CharField("Dedicação", max_length=2,
                                 choices=TIPO_DEDICACAO, null=True, blank=True,
                                 help_text="Tipo de dedicação do professor")

    areas = models.TextField(max_length=500, null=True, blank=True,
                             help_text="Áreas de Interesse do Professor")
    website = models.URLField(max_length=250, null=True, blank=True,
                              help_text="Website profissional do Professor")
    lattes = models.URLField(max_length=75, null=True, blank=True,
                             help_text="Link para o currículo Lattes do Professor")
    
    departamento = models.TextField(max_length=200, null=True, blank=True,
                                    help_text="Departamento em que o funcionário trabalha")

    email_avaliacao = models.BooleanField(default=False,
                                          help_text="Define último estado se o professor quer enviar e-mail de avaliação")

    class Meta:
        """Classe Meta."""

        verbose_name = "Professor"
        verbose_name_plural = "Professores"
        ordering = ["user"]
        permissions = (("altera_professor", "Professor altera valores"), )

    def __str__(self):
        """Retorno padrão textual do objeto."""
        return self.user.get_full_name()


class Aluno(models.Model):
    """Classe de usuários com estatus de Aluno."""

    user = models.OneToOneField(PFEUser, related_name="aluno",
                                on_delete=models.CASCADE)

    matricula = models.CharField("Matrícula", max_length=8, null=True,
                                 blank=True, help_text="Número de matrícula")

    curso2 = models.ForeignKey("operacional.Curso", null=True, blank=True, on_delete=models.SET_NULL,
                               help_text="Curso Matriculado")

    opcoes = models.ManyToManyField("projetos.Proposta", through="Opcao",
                                    help_text="Opções de projeto escolhidos")

    email_pessoal = models.EmailField(null=True, blank=True,
                                      help_text="e-mail pessoal")

    anoPFE = models.PositiveIntegerField(null=True, blank=True,
                                         validators=[MinValueValidator(2018),
                                                     MaxValueValidator(3018)],
                                         help_text="Ano que cursará o Capstone")

    semestrePFE = models.PositiveIntegerField(null=True, blank=True,
                                              validators=[MinValueValidator(1),
                                                          MaxValueValidator(2)],
                                              help_text="Semestre que cursará o Capstone")

    trancado = models.BooleanField(default=False,
                                   help_text="Caso o aluno tenha trancado ou abandonado o curso")

    cr = models.FloatField(default=0, help_text="Coeficiente de Rendimento")

    pre_alocacao = models.ForeignKey("projetos.Proposta", null=True, blank=True, on_delete=models.SET_NULL,
                                     related_name="aluno_pre_alocado",
                                     help_text="proposta pre alocada")

    trabalhou = models.TextField(max_length=1000, null=True, blank=True,
                                 help_text="Trabalhou/trabalha ou estagio/estagia em alguma empresa de tecnologia?")

    social = models.TextField(max_length=1000, null=True, blank=True,
                              help_text="Já participou de atividade sociais?")

    entidade = models.TextField(max_length=1000, null=True, blank=True,
                                help_text="Já participou de alguma entidade estudantil do Insper?")

    familia = models.TextField(max_length=1000, null=True, blank=True,\
                               help_text="Possui familiares em empresa que está aplicando? Ou empresa concorrente?")

    externo = models.CharField("Externo", max_length=40, null=True, blank=True,
                               help_text="Instituição de onde o estudante vem")

    estrela = models.BooleanField(default=False,
                                  help_text="Algum ponto de observação para a alocação do estudante em um grupo")

    # https://bradmontgomery.net/blog/django-hack-help-text-modal-instance/
    def _get_help_text(self, field_name):
        """Given a field name, return it's help text."""
        for field in self._meta.fields:
            if field.name == field_name:
                return field.help_text

    def __init__(self, *args, **kwargs):
        """Inicia objeto."""
        # Call the superclass first; it'll create all of the field objects.
        super(Aluno, self).__init__(*args, **kwargs)

        # Again, iterate over all of our field objects.
        for field in self._meta.fields:
            # Create a string, get_FIELDNAME_help text
            method_name = "get_{0}_help_text".format(field.name)

            # We can use curry to create the method with a pre-defined argument
            curried_method = partial(self._get_help_text,
                                     field_name=field.name)

            # And we add this method to the instance of the class.
            setattr(self, method_name, curried_method)

    def get_curso(self):
        """Retorna em string o nome do curso."""
        if self.curso2:
            return str(self.curso2)
        return "Sem curso"

    # Usar get_curso_display em vez disso
    def get_curso_completo(self):
        """Retorna em string com o nome completo do curso."""
        if self.curso2:
            return str(self.curso2)
        return "Sem curso"

    @property
    def get_alocacoes(self):
        """Retorna alocações do estudante."""
        alocacoes = {}  # dicionário para cada alocação do estudante
        todas_alocacao = Alocacao.objects.filter(aluno=self.pk)
        for alocacao in todas_alocacao:
            ano_semestre = str(alocacao.projeto.ano) + "." + str(alocacao.projeto.semestre)
            alocacoes[ano_semestre] = alocacao
        return alocacoes

    class Meta:
        """Meta para Aluno."""
        ordering = ["user"]
        permissions = ()

    def __str__(self):
        """Retorna o nome completo do estudante."""
        return self.user.get_full_name()


class Opcao(models.Model):
    """Opções de Projetos pelos Alunos com suas prioridades."""

    proposta = models.ForeignKey("projetos.Proposta", null=True, blank=True,
                                 on_delete=models.SET_NULL)

    aluno = models.ForeignKey(Aluno, null=True, blank=True,
                              on_delete=models.CASCADE)

    prioridade = models.PositiveSmallIntegerField()

    class Meta:
        """Meta para Opcao."""
        verbose_name = "Opção"
        verbose_name_plural = "Opções"
        ordering = ["prioridade"]
        permissions = (("altera_professor", "Professor altera valores"), )

    def __str__(self):
        """Retorno padrão textual do objeto."""
        mensagem = ""
        if self.aluno and self.aluno.user and self.aluno.user.username:
            mensagem += self.aluno.user.username
        mensagem += " >>> "
        if self.proposta and self.proposta.titulo:
            mensagem += self.proposta.titulo
        return mensagem


class OpcaoTemporaria(models.Model):
    """Opções Temporárias de Projetos pelos Alunos com suas prioridades."""

    proposta = models.ForeignKey("projetos.Proposta", null=True, blank=True,
                                 on_delete=models.SET_NULL)

    aluno = models.ForeignKey(Aluno, null=True, blank=True,
                              on_delete=models.CASCADE)

    prioridade = models.PositiveSmallIntegerField(null=True, blank=True,)

    class Meta:
        """Meta para OpcaoTemporaria."""
        verbose_name = "Opção Temporária"
        verbose_name_plural = "Opções Temporárias"
        ordering = ["prioridade"]

    def __str__(self):
        """Retorno padrão textual do objeto."""
        mensagem = ""
        if self.aluno and self.aluno.user and self.aluno.user.username:
            mensagem += self.aluno.user.username
        mensagem += " >>> "
        if self.proposta and self.proposta.organizacao.sigla and self.proposta.titulo:
            mensagem += "[" + self.proposta.organizacao.sigla + "] " + self.proposta.titulo
        mensagem += " := " + str(self.prioridade)
        return mensagem


class Alocacao(models.Model):
    """Projeto em que o aluno está alocado."""

    projeto = models.ForeignKey("projetos.Projeto", on_delete=models.CASCADE)
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE)

    avaliacao_intermediaria = models.DateTimeField("Avaliação Intermediária", default=None, blank=True, null=True,
                                                   help_text="Momento em que o orientador verificou a avaliação intermediária de par do estudante")
    
    avaliacao_final = models.DateTimeField("Avaliação Final", default=None, blank=True, null=True,
                                            help_text="Momento em que o orientador verificou a avaliação final de par do estudante")

    horarios = models.CharField(max_length=512, null=True, blank=True, help_text="Horários alocados para trabalhar no projeto")
    
    class Meta:
        """Meta para Alocacao."""
        verbose_name = "Alocação"
        verbose_name_plural = "Alocações"
        permissions = (("altera_professor", "Professor altera valores"), )
        ordering = ["projeto__ano", "projeto__semestre", "-aluno__externo",]

    def __str__(self):
        """Retorno padrão textual do objeto."""
        return self.aluno.user.username+" >>> "+self.projeto.get_titulo()


class UsuarioEstiloComunicacao(models.Model):
    usuario = models.ForeignKey(PFEUser, on_delete=models.CASCADE)
    estilo_comunicacao = models.ForeignKey("estudantes.EstiloComunicacao", on_delete=models.CASCADE)
    prioridade_resposta1 = models.IntegerField(choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4')])
    prioridade_resposta2 = models.IntegerField(choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4')])
    prioridade_resposta3 = models.IntegerField(choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4')])
    prioridade_resposta4 = models.IntegerField(choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4')])

    def clean(self):
        # Ensure that all priority fields have unique values
        priorities = [
            self.prioridade_resposta1,
            self.prioridade_resposta2,
            self.prioridade_resposta3,
            self.prioridade_resposta4,
        ]
        if len(priorities) != len(set(priorities)):
            raise ValidationError("Cada prioridade deve ser única.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def get_score_estilo(estilo):

        # List of priorities
        priorities = [
            (estilo.prioridade_resposta1, 6),
            (estilo.prioridade_resposta2, 4),
            (estilo.prioridade_resposta3, 3),
            (estilo.prioridade_resposta4, 1),
        ]

        sorted_priorities = sorted(priorities, key=lambda x: x[0])
        sorted_first_columns = [item[1] for item in sorted_priorities]

        return sorted_first_columns

    def __str__(self):
        return f"{self.usuario.get_full_name} - {self.estilo_comunicacao.questao}"

    class Meta:
        unique_together = ("usuario", "estilo_comunicacao")


class Parceiro(models.Model):  # da empresa
    """Classe de usuários com estatus de Parceiro (das organizações)."""

    user = models.OneToOneField(PFEUser, related_name="parceiro",
                                on_delete=models.CASCADE,
                                help_text="Identificaçãdo do usuário")
    
    organizacao = models.ForeignKey("projetos.Organizacao", on_delete=models.CASCADE,
                                    blank=True, null=True,
                                    help_text="Organização Parceira")
    
    cargo = models.CharField("Cargo", max_length=90, blank=True,
                             help_text="Cargo Funcional")
    
    principal_contato = models.BooleanField("Principal Contato", default=False)

    class Meta:
        """Meta para Parceiro."""

        ordering = ["user"]
        permissions = (("altera_parceiro", "Parceiro altera valores"),)

    def __str__(self):
        """Retorno padrão textual do objeto."""
        if self.organizacao:
            return self.user.get_full_name()+" ["+self.organizacao.sigla+"]"

        return self.user.get_full_name()


class Administrador(models.Model):
    """Classe de usuários com estatus de Administrador."""

    user = models.OneToOneField(PFEUser, related_name="administrador",
                                on_delete=models.CASCADE)
    
    assinatura = models.ImageField("Assinatura", upload_to=get_upload_path, null=True, blank=True,
                                help_text="Assinatura do coordenador")

    nome_para_certificados = models.CharField(max_length=128, null=True, blank=True,
                                           help_text="Nome para assinatura do coordenador do Capstone")

    class Meta:
        """Meta para Administrador."""
        verbose_name = "Administrador"
        verbose_name_plural = "Administradores"
        ordering = ["user"]
        permissions = (("altera_empresa", "Empresa altera valores"),
                       ("altera_professor", "Professor altera valores"), )

    def __str__(self):
        """Retorno padrão textual do objeto."""
        return self.user.get_full_name()
    
    def coordenador_email(self):
        if self.nome_para_certificados:
            return quote(self.nome_para_certificados)
        return ""
