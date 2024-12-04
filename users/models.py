#!/usr/bin/env python
#pylint: disable=unused-argument
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Maio de 2019
"""

import datetime
import re
from hashids import Hashids
from urllib.parse import quote
import logging

from decimal import Decimal, ROUND_HALF_UP

from functools import partial

from django.conf import settings

from django.http import HttpResponse

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models.functions import Lower
from django.db.models import F


from projetos.models import Projeto, Proposta, Organizacao, Avaliacao2, Banca
from projetos.models import ObjetivosDeAprendizagem, Reprovacao, Evento, Certificado
from projetos.support import calcula_objetivos, get_upload_path

from operacional.models import Curso

from estudantes.models import Relato, EstiloComunicacao

from academica.models import Exame

# Get an instance of a logger
logger = logging.getLogger(__name__)

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

    def __str__(self):
        """Retorno padrão textual do objeto."""
        texto = self.get_full_name()
        if self.tipo_de_usuario == 1 and hasattr(self, 'aluno'):  # (1, 'aluno'),
            texto += " (estudante"
            if self.aluno.anoPFE and self.aluno.semestrePFE:
                texto += " : " + str(self.aluno.anoPFE) + "." + str(self.aluno.semestrePFE)
        elif self.tipo_de_usuario == 2 and hasattr(self, 'professor'):  # (2, 'professor'),
            texto += " (professor"
            if self.professor.dedicacao:
                texto += " : " + self.professor.dedicacao
        elif self.tipo_de_usuario == 3 and hasattr(self, 'parceiro'):  # (3, 'parceiro'),
            texto += " (parceiro"
            if self.parceiro.organizacao and self.parceiro.organizacao.sigla:
                texto += " : " + self.parceiro.organizacao.sigla
        elif self.tipo_de_usuario == 4:  # (4, 'administrador'),
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

    curso2 = models.ForeignKey(Curso, null=True, blank=True, on_delete=models.SET_NULL,
                             help_text="Curso Matriculado")

    opcoes = models.ManyToManyField(Proposta, through="Opcao",
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

    pre_alocacao = models.ForeignKey(Proposta, null=True, blank=True, on_delete=models.SET_NULL,
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

    def get_objetivos(self, avaliacoes):
        """Retorna objetivos."""
        lista_objetivos = {}
        avaliadores = set()

        for objetivo in ObjetivosDeAprendizagem.objects.all():
            avaliacoes_p_obj = avaliacoes.filter(objetivo=objetivo).order_by("avaliador", "-momento")
            if avaliacoes_p_obj:
                for objtmp in lista_objetivos:  # Se já existe um objetivo com a mesma sigla haverá um erro na média
                    if objtmp.sigla == objetivo.sigla:
                        raise ValidationError("<h2>Erro, dois objetivos no mesmo semestre com a mesma sigla!</h2>")
                lista_objetivos[objetivo] = {}
                for aval in avaliacoes_p_obj:
                    if aval.avaliador not in lista_objetivos[objetivo]:  # Se não for o mesmo avaliador
                        avaliadores.add(aval.avaliador)
                        if aval.na or (aval.nota is None) or (aval.peso is None):
                            lista_objetivos[objetivo][aval.avaliador] = None
                        else:
                            lista_objetivos[objetivo][aval.avaliador] = (float(aval.nota), float(aval.peso))
                    # Senão é só uma avaliação de objetivo mais antiga (E IGNORAR)

        if not lista_objetivos:
            return 0, None, None

        # média por objetivo
        val_objetivos = {}
        pes_total = 0
        for obj in lista_objetivos:  # Verificando cada objetivo de aprendizado identificado
            val = 0.0
            pes = 0.0
            count = 0
            if lista_objetivos[obj]:
                for avali in lista_objetivos[obj]:
                    if lista_objetivos[obj][avali]:
                        count += 1
                        val += lista_objetivos[obj][avali][0]
                        pes += lista_objetivos[obj][avali][1]
                        pes_total += lista_objetivos[obj][avali][1]
                if count:
                    valor = val/float(count)
                    peso = pes/float(count)
                    val_objetivos[obj] = (valor, peso)

        return val_objetivos, pes_total, avaliadores

    def get_banca(self, avaliacoes_banca):
        """Retorna média final das bancas informadas."""
        val_objetivos, pes_total, avaliadores = Aluno.get_objetivos(self, avaliacoes_banca)

        if not val_objetivos:
            return 0, None, None

        # média dos objetivos
        val = 0.0
        pes = 0.0
        for obj in val_objetivos:
            if pes_total == 0:  # Deve ser Banca Falconi
                val += val_objetivos[obj][0]
            else:
                val += val_objetivos[obj][0]*val_objetivos[obj][1]
            pes += val_objetivos[obj][1]

        if val_objetivos:
            pes = float(pes)
            if pes != 0:
                val = float(val)/pes
            else:
                val = float(val)/float(len(val_objetivos))
        else:
            pes = None

        return val, pes, avaliadores

    @property
    def get_edicoes(self):
        """Recuper as notas do Estudante."""
        edicao = {}  # dicionário para cada alocação do estudante (por exemplo DP, ou Capstone Avançado)

        alocacoes = Alocacao.objects.filter(aluno=self.pk)

        try:
            banca_intermediaria = Exame.objects.get(sigla="BI")
            banca_final = Exame.objects.get(sigla="BF")
            relatorio_planejamento = Exame.objects.get(sigla="RP")
            relatorio_intermediario_grupo = Exame.objects.get(sigla="RIG")
            relatorio_final_grupo = Exame.objects.get(sigla="RFG")
            relatorio_intermediario_individual = Exame.objects.get(sigla="RII")
            relatorio_final_individual = Exame.objects.get(sigla="RFI")
            planejamento_primeira_fase = Exame.objects.get(sigla="PPF")
            avaliacao_parcial_individual = Exame.objects.get(sigla="API")
            avaliacao_final_individual = Exame.objects.get(sigla="AFI")
            avaliacao_parcial_grupo = Exame.objects.get(sigla="APG")
            avaliacao_final_grupo = Exame.objects.get(sigla="AFG")
        except Exame.DoesNotExist:
            raise ValidationError("<h2>Erro ao identificar tipos de avaliações!</h2>")

        for alocacao in alocacoes:

            notas = []  # iniciando uma lista de notas vazia

            # Banca Intermediária (1)
            avaliacoes_banca_interm = Avaliacao2.objects.filter(projeto=alocacao.projeto, exame=banca_intermediaria)

            if avaliacoes_banca_interm:
                #nota_banca_interm, peso, avaliadores = Aluno.get_objetivos(self, avaliacoes_banca_interm, eh_banca=True)
                nota_banca_interm, peso, avaliadores = Aluno.get_objetivos(self, avaliacoes_banca_interm)
                notas.append(("BI", nota_banca_interm, peso/100 if peso else 0))

            # Banca Final (2)
            avaliacoes_banca_final = Avaliacao2.objects.filter(projeto=alocacao.projeto, exame=banca_final)

            if avaliacoes_banca_final:
                #nota_banca_final, peso, avaliadores = Aluno.get_objetivos(self, avaliacoes_banca_final, eh_banca=True)
                nota_banca_final, peso, avaliadores = Aluno.get_objetivos(self, avaliacoes_banca_final)
                notas.append(("BF", nota_banca_final, peso/100 if peso else 0))

            # vvvvvvvvvv NÃO USA OBJETIVOS DE APREENZAGEM vvvvvvvvvv
            # Relatório Preliminar (10)
            relp = Avaliacao2.objects.filter(projeto=alocacao.projeto, exame=relatorio_planejamento).\
                order_by("momento").last()
            if relp and relp.nota is not None:
                notas.append(("RPL", float(relp.nota), relp.peso/100 if relp.peso else 0))
            # ^^^^^^^^^^ NÃO USA OBJETIVOS DE APREENZAGEM ^^^^^^^^^^

            # Relatório Intermediário de Grupo (11)
            rig = Avaliacao2.objects.filter(projeto=alocacao.projeto, exame=relatorio_intermediario_grupo)

            if rig:
                nota_rig, peso, avaliadores = Aluno.get_objetivos(self, rig)
                notas.append(("RIG", nota_rig, peso/100 if peso else 0))

            # Relatório Final de Grupo (12)
            rfg = Avaliacao2.objects.filter(projeto=alocacao.projeto, exame=relatorio_final_grupo)

            if rfg:
                nota_rfg, peso, avaliadores = Aluno.get_objetivos(self, rfg)
                notas.append(("RFG", nota_rfg, peso/100 if peso else 0))

            # Relatório Intermediário Individual (21)
            rii = Avaliacao2.objects.filter(alocacao=alocacao, exame=relatorio_intermediario_individual)
            if rii:
                nota_rii, peso, avaliadores = Aluno.get_objetivos(self, rii)
                notas.append(("RII", nota_rii, peso/100 if peso else 0))

            # Relatório Final Individual (22)
            rfi = Avaliacao2.objects.filter(alocacao=alocacao,exame=relatorio_final_individual)
            if rfi:
                nota_rfi, peso, avaliadores = Aluno.get_objetivos(self, rfi)
                notas.append(("RFI", nota_rfi, peso/100 if peso else 0))

            # NÃO MAIS USADAS, FORAM USADAS QUANDO AINDA EM DOIS SEMESTRES
            # Planejamento Primeira Fase  (50)
            ppf = Avaliacao2.objects.filter(projeto=alocacao.projeto, exame=planejamento_primeira_fase).\
                order_by("momento").last()
            if ppf:
                notas.append(("PPF", float(ppf.nota), ppf.peso/100))

            # Avaliação Parcial Individual (51)
            api = Avaliacao2.objects.filter(alocacao=alocacao, exame=avaliacao_parcial_individual)
            if api:
                nota_api, peso, avaliadores = Aluno.get_objetivos(self, api)
                notas.append(("API", nota_api, peso/100))

            # Avaliação Final Individual (52),
            afi = Avaliacao2.objects.filter(alocacao=alocacao, exame=avaliacao_final_individual)
            if afi:
                nota_afi, peso, avaliadores = Aluno.get_objetivos(self, afi)
                notas.append(("AFI", nota_afi, peso/100))

            # Avaliação Parcial de Grupo (53)
            apg = Avaliacao2.objects.filter(projeto=alocacao.projeto, exame=avaliacao_parcial_grupo)
            if apg:
                nota_apg, peso, avaliadores = Aluno.get_objetivos(self, apg)
                notas.append(("APG", nota_apg, peso/100))

            # Avaliação Final de Grupo (54)
            afg = Avaliacao2.objects.filter(projeto=alocacao.projeto, exame=avaliacao_final_grupo)
            if afg:
                nota_afg, peso, avaliadores = Aluno.get_objetivos(self, afg)
                notas.append(("AFG", nota_afg, peso/100))

            edicao[str(alocacao.projeto.ano)+"."+str(alocacao.projeto.semestre)] = notas

        return edicao

    #@property
    def get_notas(self, request=None, ano=None, semestre=None, checa_banca=True):
        """Recuper as notas do Estudante."""
        edicao = {}  # dicionário para cada alocação do estudante

        if ano and semestre:
            alocacoes = Alocacao.objects.filter(aluno=self.pk, projeto__ano=ano,projeto__semestre=semestre)
        else:
            alocacoes = Alocacao.objects.filter(aluno=self.pk)

        now = datetime.datetime.now()

        # Sigla, Nome, Grupo, Nota/Check, Banca
        pavaliacoes = [
            ("RP", "Relatório Preliminar", True, False, -1),
            ("RII", "Relatório Intermediário Individual", False, True, -1),
            ("RIG", "Relatório Intermediário de Grupo", True, True, -1),
            ("RFG", "Relatório Final de Grupo", True, True, -1),
            ("RFI", "Relatório Final Individual", False, True, -1),
            # NÃO MAIS USADAS, FORAM USADAS QUANDO AINDA EM DOIS SEMESTRES
            ("PPF", "Planejamento Primeira Fase", True, False, -1),
            ("API", "Avaliação Parcial Individual", False, True, -1),
            ("AFI", "Avaliação Final Individual", False, True, -1),
            ("APG", "Avaliação Parcial de Grupo", True, True, -1),
            ("AFG", "Avaliação Final de Grupo", True, True, -1),
            ("P", "Probation", False, True, -1),
            ("BI", "Banca Intermediária", True, True, 1),
            ("BF", "Banca Final", True, True, 0),
        ]

        for alocacao in alocacoes:
            
            notas = []  # iniciando uma lista de notas vazia

            for pa in pavaliacoes:
                banca = None
                if pa[4] >= 0:  # Banca
                    banca = Banca.objects.filter(projeto=alocacao.projeto, tipo_de_banca=pa[4]).last()
                    
                try:
                    exame=Exame.objects.get(sigla=pa[0])
                    if pa[2]:  # GRUPO
                        paval = Avaliacao2.objects.filter(projeto=alocacao.projeto, exame=exame)
                    else:  # INDIVIDUAL
                        paval = Avaliacao2.objects.filter(alocacao=alocacao, exame=exame)

                    if paval:

                        if pa[4] >= 0 and banca:  # Banca
                            valido = True  # Verifica se todos avaliaram a pelo menos 24 horas atrás

                            if checa_banca:
                                if (request is None) or (request.user.tipo_de_usuario not in [2,4]):  # Se não for professor/administrador
                                    for membro in banca.membros():
                                        avaliacao = paval.filter(avaliador=membro).last()
                                        if (not avaliacao) or (now - avaliacao.momento < datetime.timedelta(hours=24)):
                                            valido = False
                                    if banca.tipo_de_banca in [0, 1]: # Banca Final ou Intermediária também precisam da avaliação do orientador
                                        avaliacao = paval.filter(avaliador=alocacao.projeto.orientador.user).last()
                                        if (not avaliacao) or (now - avaliacao.momento < datetime.timedelta(hours=24)):
                                            valido = False

                            if valido:
                                pnota, ppeso, _ = Aluno.get_banca(self, paval)
                                notas.append((pa[0], pnota, ppeso/100 if ppeso else 0, pa[1]))
                        else:
                            if pa[3]:  # Nota
                                pnota, ppeso, _ = Aluno.get_banca(self, paval)
                                notas.append((pa[0], pnota, ppeso/100 if ppeso else 0, pa[1]))
                            else:  # Check
                                pnp = paval.order_by("momento").last()
                                notas.append((pa[0], float(pnp.nota) if pnp.nota else None, pnp.peso/100 if pnp.peso else 0, pa[1]))
    
                except Exame.DoesNotExist:
                    raise ValidationError("<h2>Erro ao identificar tipos de avaliações!</h2>")

            key = f"{alocacao.projeto.ano}.{alocacao.projeto.semestre}"
            if key in edicao:
                logger.error("Erro, duas alocações no mesmo semestre!")
                raise ValidationError("<h2>Erro, duas alocações no mesmo semestre!</h2>")
            edicao[key] = notas

        return edicao

    # CREIO QUE NÃO ESTÁ SENDO USADO
    # @property
    # def get_medias(self):
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

    proposta = models.ForeignKey(Proposta, null=True, blank=True,
                                 on_delete=models.SET_NULL)

    aluno = models.ForeignKey(Aluno, null=True, blank=True,
                              on_delete=models.CASCADE)

    prioridade = models.PositiveSmallIntegerField()

    class Meta:
        """Meta para Opcao."""
        verbose_name = 'Opção'
        verbose_name_plural = 'Opções'
        ordering = ['prioridade']
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

    proposta = models.ForeignKey(Proposta, null=True, blank=True,
                                 on_delete=models.SET_NULL)

    aluno = models.ForeignKey(Aluno, null=True, blank=True,
                              on_delete=models.CASCADE)

    prioridade = models.PositiveSmallIntegerField(null=True, blank=True,)

    class Meta:
        """Meta para OpcaoTemporaria."""

        verbose_name = 'Opção Temporária'
        verbose_name_plural = 'Opções Temporárias'
        ordering = ['prioridade']

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

    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE)
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
    def get_edicoes(self):
        """Retorna objetivos."""
        edicoes = self.aluno.get_edicoes
        semestre = str(self.projeto.ano)+"."+str(self.projeto.semestre)
        if semestre in edicoes:
            return edicoes[semestre]
        return None

    # @property
    def get_notas(self, checa_banca=True):
        """Retorna notas do estudante no projeto."""
        edicoes = self.aluno.get_notas(ano=self.projeto.ano, semestre=self.projeto.semestre, checa_banca=checa_banca)
        return edicoes[str(self.projeto.ano)+"."+str(self.projeto.semestre)]

    @property
    def get_media(self):
        """Retorna média e peso final."""
        reprovacao = Reprovacao.objects.filter(alocacao=self)
        if reprovacao:
            return {"media": reprovacao.last().nota, "pesos": 1}

        edicao = self.get_notas()

        nota_final = 0
        nota_individual = 0
        nota_grupo_inter = 0
        nota_grupo_final = 0
        peso_final = 0
        peso_individual = 0
        peso_grupo_inter = 0
        peso_grupo_final = 0
        for aval, nota, peso, _ in edicao:
            if aval is not None and nota is not None and peso is not None:
                peso_final += peso
                nota_final += nota * peso
                if aval in ("RII", "RFI", "API", "AFI"):
                    peso_individual += peso
                    nota_individual += nota * peso
                if aval in ("RIG", "APG", "RPL", "PPF"):
                    peso_grupo_inter += peso
                    nota_grupo_inter += nota * peso
                if aval in ("RFG", "AFG"):
                    peso_grupo_final += peso
                    nota_grupo_final += nota * peso
        peso_final = round(peso_final, 2)

        individual = None
        if peso_individual > 0:
            individual = nota_individual/peso_individual

        # Arredonda os valores finais para auxiliar do check de peso 100% e média 5.
        nota_final = round(nota_final, 6)
        peso_final = round(peso_final, 9)

        return {
            "media": nota_final,
            "pesos": peso_final,
            "peso_grupo_inter": peso_grupo_inter,
            "nota_grupo_inter": nota_grupo_inter,
            "peso_grupo_final": peso_grupo_final,
            "nota_grupo_final": nota_grupo_final,
            "individual": individual,
        }

    @property
    def get_medias_oo(self):
        """Retorna OOs."""
        alocacoes = Alocacao.objects.filter(id=self.id)
        context = calcula_objetivos(alocacoes)
        return context

    @property
    def media(self):
        """Retorna média final."""
        return self.get_media["media"]

    @property
    def peso(self):
        """Retorna peso final."""
        return self.get_media["pesos"]

    @property
    def get_relatos(self):
        """Retorna todos os possiveis relatos quinzenais da alocacao."""
        
        if self.projeto.semestre == 1:
            eventos = Evento.objects.filter(tipo_de_evento=20, endDate__year=self.projeto.ano, endDate__month__lt=7).order_by('endDate')
        else:
            eventos = Evento.objects.filter(tipo_de_evento=20, endDate__year=self.projeto.ano, endDate__month__gt=6).order_by('endDate')

        relatos = []
        # avals = []

        for index in range(len(eventos)):
            if not index: # index == 0:
                relato = Relato.objects.filter(alocacao=self, momento__lte=eventos[0].endDate + datetime.timedelta(days=1)).order_by('momento').last()
            else:
                relato = Relato.objects.filter(alocacao=self, momento__gt=eventos[index-1].endDate + datetime.timedelta(days=1), momento__lte=eventos[index].endDate + datetime.timedelta(days=1)).order_by('momento').last()
            relatos.append(relato)

        return zip(eventos, relatos, range(len(eventos)))

    @property
    def get_certificados(self):
        """Retorna todos os certificados recebidos pelo estudante nessa alocação."""
        certificados = Certificado.objects.filter(usuario=self.aluno.user, projeto=self.projeto)
        return certificados
    
    def get_bancas(self):
        """Retorna as bancas que estudante participou."""
        bancas_proj = Banca.objects.filter(projeto=self.projeto)
        bancas_prob = Banca.objects.filter(alocacao=self)
        return bancas_proj | bancas_prob


class UsuarioEstiloComunicacao(models.Model):
    usuario = models.ForeignKey(PFEUser, on_delete=models.CASCADE)
    estilo_comunicacao = models.ForeignKey(EstiloComunicacao, on_delete=models.CASCADE)
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

    def get_respostas_in_order(self):
        estilos = [
            self.estilo_comunicacao.resposta1,
            self.estilo_comunicacao.resposta2,
            self.estilo_comunicacao.resposta3,
            self.estilo_comunicacao.resposta4,
        ]
        respostas = [
            (self.prioridade_resposta1, estilos[self.prioridade_resposta1-1]),
            (self.prioridade_resposta2, estilos[self.prioridade_resposta2-1]),
            (self.prioridade_resposta3, estilos[self.prioridade_resposta3-1]),
            (self.prioridade_resposta4, estilos[self.prioridade_resposta4-1]),
        ]
        return respostas
    
    def get_score(self):

        # List of priorities
        priorities = [
            (self.prioridade_resposta1, 6),
            (self.prioridade_resposta2, 4),
            (self.prioridade_resposta3, 3),
            (self.prioridade_resposta4, 1),
        ]

        # Sort the priorities list by the second element of each tuple
        sorted_priorities = sorted(priorities, key=lambda x: x[0])

        # Extract the first element of each sorted tuple into a new list
        sorted_first_columns = [item[1] for item in sorted_priorities]

        return sorted_first_columns

    
    def get_respostas(usuario):
     
        valores = {
                "PR_Fav": 0,  # Pragmático - Escorre em Condições Favoráveis
                "PR_Str": 0,  # Pragmático - Escorre em Condições de Stress
                "S_Fav": 0,   # Afetivo - Escorre em Condições Favoráveis
                "S_Str": 0,   # Afetivo - Escorre em Condições de Stress
                "PN_Fav": 0,  # PN - Escorre em Condições Favoráveis
                "PN_Str": 0,  # PN - Escorre em Condições de Stress
                "I_Fav": 0,   # I - Escorre em Condições Favoráveis
                "I_Str": 0,   # I - Escorre em Condições de Stress
            }

        estilos = estilos = UsuarioEstiloComunicacao.objects.filter(usuario=usuario).exists()
        if not estilos:
            return None
        
        # PR_Fav = A1 + G1 + M1 + B3 + H3 + N3 + C4 + I4 + O4  # D5+D35+D65+D12+D42+D72+D18+D48+D78
        # PR_Str = D3 + J3 + P3 + E3 + K3 + Q3 + F2 + L2 + R2  # D22+D52+D82+D27+D57+D87+D31+D61+D91
        # S_Fav = A2 + G2 + M2 + B1 + H1 + N1 + O3 + I3 + C3  # D6+D36+D66+D10+D40+D70+D77+D47+D17
        # S_Str = D4 + J4 + P4 + E1 + K1 + Q1 + F4 + L4 + R4  # D23+D53+D83+D25+D55+D85+D33+D63+D93
        # PN_Fav = A3 + M3 + G3 + B2 + H3 + N2 + C2 + I2 + O2  # D7+D67+D37+D11+D41+D71+D16+D46+D76
        # PN_Str = D1 + J1 + P1 + E2 + K2 + Q2 + F1 + L1 + R1  # D20+D50+D80+D26+D56+D86+D30+D60+D90
        # I_Fav = A4 + G4 + M4 + B4 + H4 + N4 + C1 + I1 + O1  # D8+D38+D68+D13+D43+D73+D15+D45+D75
        # I_Str = D2 + J2 + P2 + E4 + K4 + Q4 + R3 + L3 + F3  # D21+D51+D81+D28+D58+D88+D92+D62+D32

        tabela = {
            "PR_Fav": ["A0", "G0", "M0", "B2", "H2", "N2", "C3", "I3", "O3"],
            "PR_Str": ["D2", "J2", "P2", "E2", "K2", "Q2", "F1", "L1", "R1"],
            "S_Fav": ["A1", "G1", "M1", "B0", "H0", "N0", "O2", "I2", "C2"],
            "S_Str": ["D3", "J3", "P3", "E0", "K0", "Q0", "F3", "L3", "R3"],
            "PN_Fav": ["A2", "M2", "G2", "B1", "H1", "N1", "C1", "I1", "O1"],
            "PN_Str": ["D0", "J0", "P0", "E1", "K1", "Q1", "F0", "L0", "R0"],
            "I_Fav": ["A3", "G3", "M3", "B3", "H3", "N3", "C0", "I0", "O0"],
            "I_Str": ["D1", "J1", "P1", "E3", "K3", "Q3", "R2", "L2", "F2"],
        }

        for estilo in EstiloComunicacao.objects.all():
            usuario_estilo = UsuarioEstiloComunicacao.objects.filter(usuario=usuario, estilo_comunicacao=estilo).last()
            if usuario_estilo and estilo.bloco:
                respostas = usuario_estilo.get_score()
                for k, v in tabela.items():
                    for i in v:
                        if i[0] == estilo.bloco:
                            valores[k] += respostas[int(i[1])]

        return {
            "Pragmático Favorável": valores["PR_Fav"],
            "Pragmático Stress": valores["PR_Str"],
            "Afetivo Favorável": valores["S_Fav"],
            "Afetivo Stress": valores["S_Str"],
            "Racional Favorável": valores["PN_Fav"],
            "Racional Stress": valores["PN_Str"],
            "Reflexivo Favorável": valores["I_Fav"],
            "Reflexivo Stress": valores["I_Str"],
            "TOTAL Favorável": valores["PR_Fav"] + valores["S_Fav"] + valores["PN_Fav"] + valores["I_Fav"],
            "TOTAL Stress": valores["PR_Str"] + valores["S_Str"] + valores["PN_Str"] + valores["I_Str"],
        }
        

    def __str__(self):
        return f"{self.usuario.get_full_name} - {self.estilo_comunicacao.questao}"

    class Meta:
        unique_together = ("usuario", "estilo_comunicacao")


class Parceiro(models.Model):  # da empresa
    """Classe de usuários com estatus de Parceiro (das organizações)."""

    user = models.OneToOneField(PFEUser, related_name='parceiro',
                                on_delete=models.CASCADE,
                                help_text='Identificaçãdo do usuário')
    organizacao = models.ForeignKey(Organizacao, on_delete=models.CASCADE,
                                    blank=True, null=True,
                                    help_text='Organização Parceira')
    cargo = models.CharField("Cargo", max_length=90, blank=True,
                             help_text='Cargo Funcional')
    principal_contato = models.BooleanField("Principal Contato", default=False)

    class Meta:
        """Meta para Parceiro."""

        ordering = ['user']
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
