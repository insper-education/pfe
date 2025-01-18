#!/usr/bin/env python
#pylint: disable=unused-argument
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Maio de 2019
"""

import inspect   # TEMPORARIAMENTE PARA DEBUG

# import datetime
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

# from academica.models import Exame
# from projetos.models import Avaliacao2
# from projetos.models import Banca
# from projetos.models import Evento
#from projetos.models import ObjetivosDeAprendizagem
#from operacional.models import Curso
#from estudantes.models import Relato
#from estudantes.models import EstiloComunicacao
#from projetos.models import Certificado
#from projetos.models import Reprovacao
#from projetos.support3 import calcula_objetivos
#from academica.support3 import get_media_alocacao_i
#from academica.support2 import get_objetivos

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

    @classmethod
    def create(cls):
        """Cria um objeto (entrada) em PFEUser."""
        user = cls()
        return user
    
    def estud(self):
        """Retorna se é estudante."""
        return self.tipo_de_usuario == 1

    def prof(self):
        """Retorna se é professor (ou Administrador)."""
        return self.tipo_de_usuario == 2

    def prof_a(self):
        """Retorna se é professor (ou Administrador)."""
        return self.tipo_de_usuario == 2 or self.tipo_de_usuario == 4
        
    def parc(self):
        """Retorna se é parceiro."""
        return self.tipo_de_usuario == 3
    
    def admin(self):
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

    @classmethod
    def create(cls, usuario):
        """Cria um Professor e já associa o usuário."""
        professor = cls(user=usuario)
        return professor


class Aluno(models.Model):
    """Classe de usuários com estatus de Aluno."""

    user = models.OneToOneField(PFEUser, related_name="aluno",
                                on_delete=models.CASCADE)

    matricula = models.CharField("Matrícula", max_length=8, null=True,
                                 blank=True,
                                 help_text="Número de matrícula")

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

    cr = models.FloatField(default=0,
                           help_text="Coeficiente de Rendimento")

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

    def get_banca_estudante(self, avaliacoes_banca):
        function_name = inspect.currentframe().f_code.co_name
        for i in range(16):
            print(f"** {function_name} não é mais um atributo de Alocacao. VERIFICAR ALTERNATIVA ************")
        raise NotImplementedError(f"{function_name} não é mais um atributo de Alocacao. VERIFICAR ALTERNATIVA")
    #     """Retorna média final das bancas informadas."""
    #     val_objetivos, pes_total, avaliadores = get_objetivos(self, avaliacoes_banca)

    #     if not val_objetivos:
    #         return 0, None, None

    #     # média dos objetivos
    #     val = 0.0
    #     pes = 0.0
    #     for obj in val_objetivos:
    #         if pes_total == 0:  # Deve ser Banca Falconi
    #             val += val_objetivos[obj][0]
    #         else:
    #             val += val_objetivos[obj][0]*val_objetivos[obj][1]
    #         pes += val_objetivos[obj][1]

    #     if val_objetivos:
    #         pes = float(pes)
    #         if pes != 0:
    #             val = float(val)/pes
    #         else:
    #             val = float(val)/float(len(val_objetivos))
    #     else:
    #         pes = None

    #     return val, pes, avaliadores

    #@property
    def get_edicoes_aluno(self):
        function_name = inspect.currentframe().f_code.co_name
        for i in range(16):
            print(f"** {function_name} não é mais um atributo de Alocacao. VERIFICAR ALTERNATIVA ************")
        raise NotImplementedError(f"{function_name} não é mais um atributo de Alocacao. VERIFICAR ALTERNATIVA")
    #     """Recuper as notas do Estudante."""
    #     edicao = {}  # dicionário para cada alocação do estudante (por exemplo DP, ou Capstone Avançado)

    #     siglas = [
    #         ("BI", "O"),
    #         ("BF", "O"), 
    #         ("RP", "N"), 
    #         ("RIG", "O"), 
    #         ("RFG", "O"), 
    #         ("RII", "I"), 
    #         ("RFI", "I"), 
    #         # NÃO MAIS USADAS, FORAM USADAS QUANDO AINDA EM DOIS SEMESTRES
    #         ("PPF", "N"), 
    #         ("API", "NI"), 
    #         ("AFI", "NI"), 
    #         ("APG", "O"), 
    #         ("AFG", "O"),
    #         ]
    #     exame = {}

    #     exame = {sigla: Exame.objects.get(sigla=sigla) for sigla, _ in siglas}

    #     alocacoes = Alocacao.objects.filter(aluno=self.pk)
    #     for alocacao in alocacoes:

    #         notas = []  # iniciando uma lista de notas vazia

    #         for sigla, tipo in siglas:
    #             if tipo == "O":  # Avaliações de Objetivos
    #                 avaliacoes = Avaliacao2.objects.filter(projeto=alocacao.projeto, exame=exame[sigla])
    #             elif tipo == "I":  # Individual
    #                 avaliacoes = Avaliacao2.objects.filter(alocacao=alocacao, exame=exame[sigla])
    #             elif tipo == "N":  # Notas
    #                 avaliacoes = Avaliacao2.objects.filter(projeto=alocacao.projeto, exame=exame[sigla])
    #                 avaliacao = avaliacoes.order_by("momento").last()
    #                 if avaliacao and avaliacao.nota is not None:
    #                     notas.append((sigla, float(avaliacao.nota), avaliacao.peso / 100 if avaliacao.peso else 0))
    #                 continue
    #             elif tipo == "NI":  # Notas Individuais
    #                 avaliacoes = Avaliacao2.objects.filter(alocacao=alocacao, exame=exame[sigla])

    #             if avaliacoes:
    #                 if tipo in ["O", "I", "NI"]:
    #                     nota, peso, _ = get_objetivos(self, avaliacoes)
    #                     notas.append((sigla, nota, peso / 100 if peso else 0))

    #         edicao[f"{alocacao.projeto.ano}.{alocacao.projeto.semestre}"] = notas

    #     return edicao
    

    def get_notas_estudante(self, request=None, ano=None, semestre=None, checa_banca=True):
        function_name = inspect.currentframe().f_code.co_name
        for i in range(16):
            print(f"** {function_name} não é mais um atributo de Alocacao. VERIFICAR ALTERNATIVA ************")
        raise NotImplementedError(f"{function_name} não é mais um atributo de Alocacao. VERIFICAR ALTERNATIVA")
    #     """Recuper as notas do Estudante."""
    #     edicao = {}  # dicionário para cada alocação do estudante

    #     if ano and semestre:
    #         alocacoes = Alocacao.objects.filter(aluno=self.pk, projeto__ano=ano,projeto__semestre=semestre)
    #     else:
    #         alocacoes = Alocacao.objects.filter(aluno=self.pk)

    #     now = datetime.datetime.now()

    #     # Sigla, Nome, Grupo, Nota/Check, Banca
    #     pavaliacoes = [
    #         ("RP", "Relatório Preliminar", True, False, None),
    #         ("RII", "Relatório Intermediário Individual", False, True, None),
    #         ("RIG", "Relatório Intermediário de Grupo", True, True, None),
    #         ("BI", "Banca Intermediária", True, True, "BI"),
    #         ("RFG", "Relatório Final de Grupo", True, True, None),
    #         ("RFI", "Relatório Final Individual", False, True, None),
    #         ("BF", "Banca Final", True, True, "BF"),
    #         ("P", "Probation", False, True, "P"),
    #         # ABAIXO NÃO MAIS USADAS, FORAM USADAS QUANDO AINDA EM DOIS SEMESTRES
    #         ("PPF", "Planejamento Primeira Fase", True, False, None),
    #         ("API", "Avaliação Parcial Individual", False, True, None),
    #         ("AFI", "Avaliação Final Individual", False, True, None),
    #         ("APG", "Avaliação Parcial de Grupo", True, True, None),
    #         ("AFG", "Avaliação Final de Grupo", True, True, None),
    #         # A principio não mostra aqui as notas da certificação Falconi
    #     ]

    #     for alocacao in alocacoes:
            
    #         notas = []  # iniciando uma lista de notas vazia

    #         for pa in pavaliacoes:
    #             checa_b = checa_banca
    #             banca = None
    #             if pa[4]:  # Banca
    #                 if pa[2]:  # Grupo - Intermediária/Final
    #                     banca = Banca.objects.filter(projeto=alocacao.projeto, composicao__exame__sigla=pa[4]).last()
    #                 else:  # Individual - Probation
    #                     banca = Banca.objects.filter(alocacao=alocacao, composicao__exame__sigla=pa[4]).last()
    #             try:
    #                 exame=Exame.objects.get(sigla=pa[0])
    #                 if pa[2]:  # GRUPO
    #                     paval = Avaliacao2.objects.filter(projeto=alocacao.projeto, exame=exame)
    #                 else:  # INDIVIDUAL
    #                     paval = Avaliacao2.objects.filter(alocacao=alocacao, exame=exame)

    #                 if paval:
    #                     if pa[4] and banca:  # Banca
    #                         valido = True  # Verifica se todos avaliaram a pelo menos 24 horas atrás

    #                         # Verifica se já passou o evento de encerramento e assim liberar notas
    #                         evento = Evento.get_evento(sigla="EE", ano=alocacao.projeto.ano, semestre=alocacao.projeto.semestre)
    #                         if pa[4] != "F" and  evento:  # Não é banca probation e tem evento de encerramento
    #                             # Após o evento de encerramento liberar todas as notas
    #                             if now.date() > evento.endDate:
    #                                 checa_b = False

    #                         if checa_b:

    #                             if (request is None) or (request.user.tipo_de_usuario not in [2,4]):  # Se não for professor/administrador
    #                                 for membro in banca.membros():
    #                                     avaliacao = paval.filter(avaliador=membro).last()
    #                                     if (not avaliacao) or (now - avaliacao.momento < datetime.timedelta(hours=24)):
    #                                         valido = False
    #                                 if banca.composicao.exame.sigla in ["BI", "BF"]: # Banca Final ou Intermediária também precisam da avaliação do orientador
    #                                     avaliacao = paval.filter(avaliador=alocacao.projeto.orientador.user).last()
    #                                     if (not avaliacao) or (now - avaliacao.momento < datetime.timedelta(hours=24)):
    #                                         valido = False

    #                         if valido:
    #                             pnota, ppeso, _ = Aluno.get_banca_estudante(self, paval)
    #                             notas.append((pa[0], pnota, ppeso/100 if ppeso else 0, pa[1]))
    #                     else:
    #                         if pa[3]:  # Nota
    #                             pnota, ppeso, _ = Aluno.get_banca_estudante(self, paval)
    #                             notas.append((pa[0], pnota, ppeso/100 if ppeso else 0, pa[1]))
    #                         else:  # Check
    #                             pnp = paval.order_by("momento").last()
    #                             notas.append((pa[0], float(pnp.nota) if pnp.nota else None, pnp.peso/100 if pnp.peso else 0, pa[1]))
    
    #             except Exame.DoesNotExist:
    #                 raise ValidationError("<h2>Erro ao identificar tipos de avaliações!</h2>")

    #         key = f"{alocacao.projeto.ano}.{alocacao.projeto.semestre}"
    #         if key in edicao:
    #             logger.error("Erro, duas alocações no mesmo semestre! " + self.get_full_name() + " " + key)
    #         edicao[key] = notas

    #     return edicao

    # CREIO QUE NÃO ESTÁ SENDO USADO
    @property
    def get_medias(self):
        function_name = inspect.currentframe().f_code.co_name
        for i in range(16):
            print(f"** {function_name} não é mais um atributo de Alocacao. VERIFICAR ALTERNATIVA ************")
        raise NotImplementedError(f"{function_name} não é mais um atributo de Alocacao. VERIFICAR ALTERNATIVA")

    #     """Retorna médias."""
    #     medias = {}  # dicionário para cada alocação do estudante

    #     edicoes = self.get_notas

    #     for ano_semestre, edicao in edicoes.items():
    #         nota_final = 0
    #         peso_final = 0
    #         # for aval, nota, peso in edicao:
    #         for _, nota, peso, _ in edicao:
    #             peso_final += peso
    #             nota_final += nota * peso
    #         peso_final = round(peso_final, 2)
    #         medias[ano_semestre] = {"media": nota_final, "pesos": peso_final}

    #     alocacoes = Alocacao.objects.filter(aluno=self.pk)
    #     for alocacao in alocacoes:
    #         reprovacao = Reprovacao.objects.filter(alocacao=alocacao)
    #         if reprovacao:
    #             ano_semestre = str(alocacao.projeto.ano) + "." + str(alocacao.projeto.semestre)
    #             medias[ano_semestre] = {
    #                 "media": reprovacao.last().nota,
    #                 "pesos": 1
    #             }

    #     return medias


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

    @classmethod
    def create(cls, usuario):
        """Cria um Estudante e já associa o usuário."""
        estudante = cls(user=usuario)
        return estudante


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
        ordering = ["projeto__ano", "projeto__semestre", ]

    def __str__(self):
        """Retorno padrão textual do objeto."""
        return self.aluno.user.username+" >>> "+self.projeto.get_titulo()

    @classmethod
    def create(cls, estudante, projeto):
        """Cria um Projeto (entrada) de Alocação."""
        alocacao = cls(projeto=projeto, aluno=estudante)
        return alocacao

    @property
    def get_edicoes_alocacao(self):
        function_name = inspect.currentframe().f_code.co_name
        for i in range(16):
            print(f"** {function_name} não é mais um atributo de Alocacao. VERIFICAR ALTERNATIVA ************")
        raise NotImplementedError(f"{function_name} não é mais um atributo de Alocacao. VERIFICAR ALTERNATIVA")
    #     """Retorna objetivos."""
    #     edicoes = self.aluno.get_edicoes
    #     semestre = str(self.projeto.ano)+"."+str(self.projeto.semestre)
    #     if semestre in edicoes:
    #         return edicoes[semestre]
    #     return None

    def get_notas_alocacao(self, checa_banca=True):
        function_name = inspect.currentframe().f_code.co_name
        for i in range(16):
            print(f"** {function_name} não é mais um atributo de Alocacao. VERIFICAR ALTERNATIVA ************")
        raise NotImplementedError(f"{function_name} não é mais um atributo de Alocacao. VERIFICAR ALTERNATIVA")
    #     """Retorna notas do estudante no projeto."""
    #     edicoes = self.aluno.get_notas_estudante(ano=self.projeto.ano, semestre=self.projeto.semestre, checa_banca=checa_banca)
    #     return edicoes[str(self.projeto.ano)+"."+str(self.projeto.semestre)]
  
    def em_probation(self):
        function_name = inspect.currentframe().f_code.co_name
        for i in range(16):
            print(f"** {function_name} não é mais um atributo de Alocacao. VERIFICAR ALTERNATIVA ************")
        raise NotImplementedError(f"{function_name} não é mais um atributo de Alocacao. VERIFICAR ALTERNATIVA")
    #     """Retorna se em probation."""
    #     reprovacao = Reprovacao.objects.filter(alocacao=self).exists()
    #     if reprovacao:
    #         return False
        
    #     now = datetime.datetime.now()

    #     # Sigla, Nome, Grupo, Nota/Check, Banca
    #     pavaliacoes = [
    #         ("P", "Probation", False, True, "P"),
    #         ### CHECK SE JA FECHOU BANCA DE PROBATION PRIMEIRO ####
    #         ("RFG", "Relatório Final de Grupo", True, True, None),
    #         ("RFI", "Relatório Final Individual", False, True, None),
    #         ("BF", "Banca Final", True, True, "BF"),
    #         ("AFI", "Avaliação Final Individual", False, True, None),
    #         ("AFG", "Avaliação Final de Grupo", True, True, None),
    #     ]

    #     for pa in pavaliacoes:
    #         checa_b = True
    #         banca = None
    #         if pa[4]:  # Banca
    #             if pa[2]:  # Grupo - Intermediária/Final
    #                 banca = Banca.objects.filter(projeto=self.projeto, composicao__exame__sigla=pa[4]).last()
    #             else:  # Individual - Probation
    #                 banca = Banca.objects.filter(alocacao=self, composicao__exame__sigla=pa[4]).last()
    #         try:
    #             exame=Exame.objects.get(sigla=pa[0])
    #             if pa[2]:  # GRUPO
    #                 paval = Avaliacao2.objects.filter(projeto=self.projeto, exame=exame)
    #             else:  # INDIVIDUAL
    #                 paval = Avaliacao2.objects.filter(alocacao=self, exame=exame)

    #             if paval:
    #                 val_objetivos = None
    #                 if pa[4] and banca:  # Banca
    #                     valido = True  # Verifica se todos avaliaram a pelo menos 24 horas atrás

    #                     # Verifica se já passou o evento de encerramento e assim liberar notas
    #                     evento = Evento.get_evento(sigla="EE", ano=self.projeto.ano, semestre=self.projeto.semestre)
    #                     if evento:
    #                         # Após o evento de encerramento liberar todas as notas
    #                         if now.date() > evento.endDate:
    #                             checa_b = False

    #                     if checa_b:
    #                         for membro in banca.membros():
    #                             avaliacao = paval.filter(avaliador=membro).last()
    #                             if (not avaliacao) or (now - avaliacao.momento < datetime.timedelta(hours=24)):
    #                                 valido = False
    #                         if banca.composicao.exame.sigla in ["BI", "BF"]: # Banca Final ou Intermediária também precisam da avaliação do orientador
    #                             avaliacao = paval.filter(avaliador=self.projeto.orientador.user).last()
    #                             if (not avaliacao) or (now - avaliacao.momento < datetime.timedelta(hours=24)):
    #                                 valido = False

    #                     if valido:
    #                         val_objetivos, _, _ = get_objetivos(self, paval)

    #                 else:
    #                     val_objetivos, _, _ = get_objetivos(self, paval)

    #                 if pa[0] == "P":
    #                     if val_objetivos:
    #                         for obj in val_objetivos:
    #                             if val_objetivos[obj][0] < 5:
    #                                 return True # Se tiver algum objetivo com nota menor que 5 mantem em probation
    #                         return False  # Se não tiver nenhum objetivo com nota menor que 5 tudo OK com probation

    #                 if val_objetivos:
    #                     for obj in val_objetivos:
    #                         if val_objetivos[obj][0] < 5:
    #                             return True

    #         except Exame.DoesNotExist:
    #             raise ValidationError("<h2>Erro ao identificar tipos de avaliações!</h2>")

    #     return False

    @property
    def get_media_alocacao(self):
        function_name = inspect.currentframe().f_code.co_name
        for i in range(16):
            print(f"** {function_name} não é mais um atributo de Alocacao. VERIFICAR ALTERNATIVA ************")
        raise NotImplementedError(f"{function_name} não é mais um atributo de Alocacao. VERIFICAR ALTERNATIVA")
    #     return get_media_alocacao_i(self)
    #     """Retorna média e peso final."""
    #     reprovacao = Reprovacao.objects.filter(alocacao=self)
    #     if reprovacao:
    #         return {"media": reprovacao.last().nota, "pesos": 1}

    #     edicao = self.get_notas_alocacao()

    #     nota_final = 0
    #     nota_individual = 0
    #     nota_grupo_inter = 0
    #     nota_grupo_final = 0
    #     peso_final = 0
    #     peso_individual = 0
    #     peso_grupo_inter = 0
    #     peso_grupo_final = 0
    #     for aval, nota, peso, _ in edicao:
    #         if aval is not None and nota is not None and peso is not None:
    #             peso_final += peso
    #             nota_final += nota * peso
    #             if aval in ("RII", "RFI", "API", "AFI"):
    #                 peso_individual += peso
    #                 nota_individual += nota * peso
    #             if aval in ("RIG", "APG", "RPL", "PPF"):
    #                 peso_grupo_inter += peso
    #                 nota_grupo_inter += nota * peso
    #             if aval in ("RFG", "AFG"):
    #                 peso_grupo_final += peso
    #                 nota_grupo_final += nota * peso
    #     peso_final = round(peso_final, 2)

    #     individual = None
    #     if peso_individual > 0:
    #         individual = nota_individual/peso_individual

    #     # Arredonda os valores finais para auxiliar do check de peso 100% e média 5.
    #     nota_final = round(nota_final, 6)
    #     peso_final = round(peso_final, 9)

    #     # Caso a nota individual seja menor que 5, a nota final é a menor das notas        
    #     if individual is not None and individual < 5:
    #         if individual < nota_final:
    #             nota_final = individual

    #     # Se a nota final permite passar, mas o estudante estiver em probation, a nota final é None
    #     if nota_final > 5.0 and em_probation(self):
    #         probation = True
    #         nota_final = None
    #     else:
    #         probation = False

    #     return {
    #         "media": nota_final,
    #         "pesos": peso_final,
    #         "peso_grupo_inter": peso_grupo_inter,
    #         "nota_grupo_inter": nota_grupo_inter,
    #         "peso_grupo_final": peso_grupo_final,
    #         "nota_grupo_final": nota_grupo_final,
    #         "individual": individual,
    #         "probation": probation,
    #     }

    #@property
    def get_medias_oo(self):  # EVITAR USAR POIS MISTURA SEMESTRES (VER GET_OAS)
        function_name = inspect.currentframe().f_code.co_name
        for i in range(16):
            print(f"** {function_name} não é mais um atributo de Alocacao. VERIFICAR ALTERNATIVA ************")
        raise NotImplementedError(f"{function_name} não é mais um atributo de Alocacao. VERIFICAR ALTERNATIVA")
    #     """Retorna OOs."""
    #     alocacoes = Alocacao.objects.filter(id=self.id)
    #     context = calcula_objetivos(alocacoes)
    #     return context

    def get_oas(self, avaliacoes):
        function_name = inspect.currentframe().f_code.co_name
        for i in range(16):
            print(f"** {function_name} não é mais um atributo de Alocacao. VERIFICAR ALTERNATIVA ************")
        raise NotImplementedError(f"{function_name} não é mais um atributo de Alocacao. VERIFICAR ALTERNATIVA")
    #     """Retorna Objetivos de Aprendizagem da alocação no semestre."""
    #     oas = {}
    #     for avaliacao in avaliacoes:
    #         if avaliacao.objetivo not in oas:
    #             oas[avaliacao.objetivo] = {"conceito": []}
    #         exame = avaliacao.exame
    #         nota = avaliacao.nota
    #         peso = avaliacao.peso
    #         if nota is not None and peso is not None:
    #             oas[avaliacao.objetivo]["conceito"].append( (exame, converte_letra(nota), float(nota), float(peso)) )
    #     for oa in oas:
    #         notas = oas[oa]["conceito"]
    #         val = 0
    #         pes = 0
    #         cor = "black"
    #         for exame, _, nota, peso in notas:
    #             if exame.periodo_para_rubricas == 2:  # (2, "Final"),
    #                 if nota < 5:
    #                     cor = "darkorange"
    #             val += nota * peso
    #             pes += peso
    #         if pes:
    #             val = val/pes
    #         if val < 5:
    #             cor = "red"
    #         oas[oa]["media"] = (converte_letra(val), val, cor)
    #         oas[oa]["peso"] = pes

    #     return oas

    def get_oas_i(self):
        # avaliacoes = Avaliacao2.objects.filter(alocacao=self, exame__grupo=False)
        # return self.get_oas(avaliacoes)
        function_name = inspect.currentframe().f_code.co_name
        for i in range(16):
            print(f"** {function_name} não é mais um atributo de Alocacao. VERIFICAR ALTERNATIVA ************")
        raise NotImplementedError(f"{function_name} não é mais um atributo de Alocacao. VERIFICAR ALTERNATIVA")
    
    # # ESSE CODIGO ESTA ERRADO, POIS NAO TRATA BANCAS, E OUTRAS REPETICOES DE AVALIACOES
    def get_oas_g(self):
        function_name = inspect.currentframe().f_code.co_name
        for i in range(16):
            print(f"** {function_name} não é mais um atributo de Alocacao. VERIFICAR ALTERNATIVA ************")
        raise NotImplementedError(f"{function_name} não é mais um atributo de Alocacao. VERIFICAR ALTERNATIVA")
    #     avaliacoes = Avaliacao2.objects.filter(projeto=self.projeto, exame__grupo=True)
    #     return self.get_oas(avaliacoes)
    
    # # ESSE CODIGO ESTA ERRADO, POIS NAO TRATA BANCAS, E OUTRAS REPETICOES DE AVALIACOES
    def get_oas_t(self):
        function_name = inspect.currentframe().f_code.co_name
        for i in range(16):
            print(f"** {function_name} não é mais um atributo de Alocacao. VERIFICAR ALTERNATIVA ************")
        raise NotImplementedError(f"{function_name} não é mais um atributo de Alocacao. VERIFICAR ALTERNATIVA")
    #     avaliacoes = Avaliacao2.objects.filter(projeto=self.projeto, exame__grupo=False) | Avaliacao2.objects.filter(projeto=self.projeto, exame__grupo=True)
    #     return self.get_oas(avaliacoes)

    #@property
    def media(self):
        # """Retorna média final."""
        # return self.get_media_alocacao["media"]
        function_name = inspect.currentframe().f_code.co_name
        for i in range(16):
            print(f"** {function_name} não é mais um atributo de Alocacao. VERIFICAR ALTERNATIVA ************")
        raise NotImplementedError(f"{function_name} não é mais um atributo de Alocacao. VERIFICAR ALTERNATIVA")
    
    # @property
    def peso(self):
        # """Retorna peso final."""
        # return self.get_media_alocacao["pesos"]
        function_name = inspect.currentframe().f_code.co_name
        for i in range(16):
            print(f"** {function_name} não é mais um atributo de Alocacao. VERIFICAR ALTERNATIVA ************")
        raise NotImplementedError(f"{function_name} não é mais um atributo de Alocacao. VERIFICAR ALTERNATIVA")

    @property
    def get_relatos(self):
        function_name = inspect.currentframe().f_code.co_name
        for i in range(16):
            print(f"** {function_name} não é mais um atributo de Alocacao. VERIFICAR ALTERNATIVA ************")
        raise NotImplementedError(f"{function_name} não é mais um atributo de Alocacao. VERIFICAR ALTERNATIVA")
    #     """Retorna todos os possiveis relatos quinzenais da alocacao."""
        
    #     eventos = Evento.get_eventos(sigla="RQ", ano=self.projeto.ano, semestre=self.projeto.semestre)
    #     relatos = []
    #     for index in range(len(eventos)):
    #         if not index: # index == 0:
    #             relato = Relato.objects.filter(alocacao=self, momento__lte=eventos[0].endDate + datetime.timedelta(days=1)).order_by('momento').last()
    #         else:
    #             relato = Relato.objects.filter(alocacao=self, momento__gt=eventos[index-1].endDate + datetime.timedelta(days=1), momento__lte=eventos[index].endDate + datetime.timedelta(days=1)).order_by('momento').last()
    #         relatos.append(relato)

    #     return zip(eventos, relatos, range(len(eventos)))

    @property
    def get_certificados(self):
        function_name = inspect.currentframe().f_code.co_name
        for i in range(16):
            print(f"** {function_name} não é mais um atributo de Alocacao. VERIFICAR ALTERNATIVA ************")
        raise NotImplementedError(f"{function_name} não é mais um atributo de Alocacao. VERIFICAR ALTERNATIVA")
    #     """Retorna todos os certificados recebidos pelo estudante nessa alocação."""
    #     certificados = Certificado.objects.filter(usuario=self.aluno.user, projeto=self.projeto)
    #     return certificados
    
    def get_bancas(self):
        function_name = inspect.currentframe().f_code.co_name
        for i in range(16):
            print(f"** {function_name} não é mais um atributo de Alocacao. VERIFICAR ALTERNATIVA ************")
        raise NotImplementedError(f"{function_name} não é mais um atributo de Alocacao. VERIFICAR ALTERNATIVA")
    #     """Retorna as bancas que estudante participou."""
    #     bancas_proj = Banca.objects.filter(projeto=self.projeto)
    #     bancas_prob = Banca.objects.filter(alocacao=self)
    #     return bancas_proj | bancas_prob


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

    @classmethod
    def create(cls, usuario):
        """Cria um Parceiro e já associa o usuário."""
        parceiro = cls(user=usuario)
        return parceiro


class Administrador(models.Model):
    """Classe de usuários com estatus de Administrador."""

    user = models.OneToOneField(PFEUser,
                                related_name="administrador",
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
