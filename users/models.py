#!/usr/bin/env python
#pylint: disable=unused-argument
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Maio de 2019
"""

import datetime
from hashids import Hashids
from urllib.parse import quote

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


from projetos.models import Projeto, Proposta, Organizacao, Avaliacao2
from projetos.models import ObjetivosDeAprendizagem, Reprovacao, Evento
from projetos.support import calcula_objetivos, get_upload_path

from operacional.models import Curso

from estudantes.models import Relato

from academica.models import Exame

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
                               help_text='LinkedIn do usuário')

    membro_comite = \
        models.BooleanField("Membro do Comitê", default=False, help_text='caso membro do comitê do PFE')

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

    observacoes = models.TextField("Observações", max_length=500, blank=True,
                                   help_text="Observações")

    # Aparentemente não sendo usado mais
    # coordenacao = \
    #     models.BooleanField("Coordenação", default=False, help_text="caso coordenador do PFE")

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

    user = models.OneToOneField(PFEUser, related_name='professor', on_delete=models.CASCADE)

    TIPO_DEDICACAO = (
        ("TI", "Tempo Integral"),
        ("TP", "Tempo Parcial"),
        ("V", "Visitante"),
        ("E", "Externo"),
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

    user = models.OneToOneField(PFEUser, related_name='aluno',
                                on_delete=models.CASCADE)

    matricula = models.CharField("Matrícula", max_length=8, null=True,
                                 blank=True,
                                 help_text='Número de matrícula')

    curso2 = models.ForeignKey(Curso, null=True, blank=True, on_delete=models.SET_NULL,
                             help_text='Curso Matriculado',)    

    opcoes = models.ManyToManyField(Proposta, through='Opcao',
                                    help_text='Opcoes de projeto escolhidos')

    email_pessoal = models.EmailField(null=True, blank=True,
                                      help_text='e-mail pessoal')

    anoPFE = models.PositiveIntegerField(null=True, blank=True,
                                         validators=[MinValueValidator(2018),
                                                     MaxValueValidator(3018)],
                                         help_text='Ano que cursará o PFE')

    semestrePFE = models.PositiveIntegerField(null=True, blank=True,
                                              validators=[MinValueValidator(1),
                                                          MaxValueValidator(2)],
                                              help_text='Semestre que cursará o PFE')

    trancado = models.BooleanField(default=False,
                                   help_text='Caso o aluno tenha trancado ou abandonado o curso')

    cr = models.FloatField(default=0,
                           help_text='Coeficiente de Rendimento')

    pre_alocacao = models.ForeignKey(Proposta, null=True, blank=True, on_delete=models.SET_NULL,
                                     related_name='aluno_pre_alocado',
                                     help_text='proposta pre alocada')

    trabalhou = models.TextField(max_length=1000, null=True, blank=True,
                                 help_text='Trabalhou/trabalha ou estagio/estagia em alguma empresa de engenharia?')

    social = models.TextField(max_length=1000, null=True, blank=True,
                              help_text='Já participou de atividade sociais?')

    entidade = models.TextField(max_length=1000, null=True, blank=True,
                                help_text='Já participou de alguma entidade estudantil do Insper?')

    familia = models.TextField(max_length=1000, null=True, blank=True,\
        help_text='Possui familiares em empresa que está aplicando? Ou empresa concorrente?')

    externo = models.CharField("Externo", max_length=40, null=True, blank=True,
                               help_text='Instituição de onde o estudante vem')

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

    def get_objetivos(self, avaliacoes, eh_banca=False):
        """Retorna objetivos."""
        lista_objetivos = {}
        avaliadores = set()
        objetivos = ObjetivosDeAprendizagem.objects.all()
        for objetivo in objetivos:
            bancas = avaliacoes.filter(objetivo=objetivo).\
                order_by('avaliador', '-momento')
            if bancas:
                lista_objetivos[objetivo] = {}
            for banca in bancas:
                # Se não for o mesmo avaliador
                if banca.avaliador not in lista_objetivos[objetivo]:
                    avaliadores.add(banca.avaliador)
                    if banca.na or (banca.nota is None) or (banca.peso is None):
                        lista_objetivos[objetivo][banca.avaliador] = None
                    else:
                        lista_objetivos[objetivo][banca.avaliador] = (float(banca.nota),
                                                                      float(banca.peso))
                # Senão é só uma avaliação de objetivo mais antiga

        if not lista_objetivos:
            return 0, None, None

        # média por objetivo
        val_objetivos = {}
        pes_total = 0
        for obj in lista_objetivos:
            val = 0
            pes = 0
            count = 0
            if lista_objetivos[obj]:
                for avali in lista_objetivos[obj]:
                    if lista_objetivos[obj][avali]:
                        count += 1
                        val += lista_objetivos[obj][avali][0]
                        pes += lista_objetivos[obj][avali][1]
                        pes_total += lista_objetivos[obj][avali][1]
                if count:
                    valor = val/count
                    peso = pes/count

                    if eh_banca:
                        # Para sempre arredondar 5.5 para 6 e 6.5 para 7 por exemplo.
                        valor = float(Decimal(valor).quantize(0, ROUND_HALF_UP))
                    else:
                        valor = float(valor)

                    val_objetivos[obj] = (valor, peso)

        return val_objetivos, pes_total, avaliadores

    def get_banca(self, avaliacoes_banca, eh_banca=False):
        """Retorna média final das bancas informadas."""
        val_objetivos, pes_total, avaliadores = Aluno.get_objetivos(self, avaliacoes_banca, eh_banca=eh_banca)

        if not val_objetivos:
            return 0, None, None

        # média dos objetivos
        val = 0
        pes = 0
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
                val = float(val)/len(val_objetivos)
        else:
            pes = None

        return val, pes, avaliadores

    @property
    def get_edicoes(self):
        """Recuper as notas do Estudante."""
        edicao = {}  # dicionário para cada alocação do estudante (por exemplo DP, ou PFE Avançado)

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
                nota_banca_interm, peso, avaliadores = Aluno.get_objetivos(self,
                                                              avaliacoes_banca_interm, eh_banca=True)
                notas.append(("BI", nota_banca_interm, peso/100 if peso else 0))

            # Banca Final (2)
            avaliacoes_banca_final = Avaliacao2.objects.filter(projeto=alocacao.projeto, exame=banca_final)

            if avaliacoes_banca_final:
                nota_banca_final, peso, avaliadores = Aluno.get_objetivos(self,
                                                             avaliacoes_banca_final, eh_banca=True)
                notas.append(("BF", nota_banca_final, peso/100 if peso else 0))

            # Relatório Preliminar (10)
            relp = Avaliacao2.objects.filter(projeto=alocacao.projeto, exame=relatorio_planejamento).\
                order_by("momento").last()
            if relp:
                notas.append(("RPL", float(relp.nota), relp.peso/100 if relp.peso else 0))

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

    @property
    def get_notas(self):
        """Recuper as notas do Estudante."""
        edicao = {}  # dicionário para cada alocação do estudante

        alocacoes = Alocacao.objects.filter(aluno=self.pk)

        for alocacao in alocacoes:

            notas = []  # iniciando uma lista de notas vazia

            try:
                # Relatório Preliminar (10)
                relp = Avaliacao2.objects.filter(projeto=alocacao.projeto,
                                                exame=Exame.objects.get(sigla="RP")).\
                    order_by("momento").last()
                if relp:
                    notas.append(("RPL", float(relp.nota) if relp.nota else None, relp.peso/100 if relp.peso else 0,
                                "Relatório Preliminar"))
                    
                # Relatório Intermediário Individual (21),
                rii = Avaliacao2.objects.filter(alocacao=alocacao,
                                                exame=Exame.objects.get(sigla="RII"))

                if rii:
                    nota_rii, peso, avaliadores = Aluno.get_banca(self, rii)
                    notas.append(("RII", nota_rii, peso/100 if peso else 0,
                                "Relatório Intermediário Individual"))

                # Relatório Intermediário de Grupo (11)
                rig = Avaliacao2.objects.filter(projeto=alocacao.projeto,
                                                exame=Exame.objects.get(sigla="RIG"))

                if rig:
                    nota_rig, peso, avaliadores = Aluno.get_banca(self, rig)
                    notas.append(("RIG", nota_rig, peso/100 if peso else 0,
                                "Relatório Intermediário de Grupo"))

                # Banca Intermediária (1)
                avaliacoes_banca_interm = Avaliacao2.objects.filter(projeto=alocacao.projeto,
                                                                    exame=Exame.objects.get(sigla="BI"))
                if avaliacoes_banca_interm:
                    nota_banca_interm, peso, avaliadores = Aluno.get_banca(self,
                                                            avaliacoes_banca_interm,
                                                            eh_banca=True)
                    notas.append(("BI", nota_banca_interm, peso/100 if peso else 0,
                                "Banca Intermediária"))


                # Relatório Final Individual (22)
                rfi = Avaliacao2.objects.filter(alocacao=alocacao,
                                                exame=Exame.objects.get(sigla="RFI"))

                if rfi:
                    nota_rfi, peso, avaliadores = Aluno.get_banca(self, rfi)
                    notas.append(("RFI", nota_rfi, peso/100 if peso else 0,
                                "Relatório Final Individual"))


                # Relatório Final de Grupo (12),
                rfg = Avaliacao2.objects.filter(projeto=alocacao.projeto,
                                                exame=Exame.objects.get(sigla="RFG"))

                if rfg:
                    nota_rfg, peso, avaliadores = Aluno.get_banca(self, rfg)
                    notas.append(("RFG", nota_rfg, peso/100 if peso else 0,
                                "Relatório Final de Grupo"))

                # Banca Final (2)
                avaliacoes_banca_final = Avaliacao2.objects.filter(projeto=alocacao.projeto,
                                                                exame=Exame.objects.get(sigla="BF"))
                if avaliacoes_banca_final:
                    nota_banca_final, peso, avaliadores = Aluno.get_banca(self,
                                                            avaliacoes_banca_final,
                                                            eh_banca=True)
                    notas.append(("BF", nota_banca_final, peso/100 if peso else 0,
                                "Banca Final"))

                
                # NÃO MAIS USADAS, FORAM USADAS QUANDO AINDA EM DOIS SEMESTRES
                # Planejamento Primeira Fase  (50)
                ppf = Avaliacao2.objects.filter(projeto=alocacao.projeto,
                                                exame=Exame.objects.get(sigla="PPF")).\
                    order_by('momento').last()
                if ppf:
                    notas.append(("PPF", float(ppf.nota) if ppf.nota else None, ppf.peso/100 if ppf.peso else 0,
                                "Planejamento Primeira Fase"))

                # Avaliação Parcial Individual (51)
                api = Avaliacao2.objects.filter(alocacao=alocacao,
                                                exame=Exame.objects.get(sigla="API"))

                if api:
                    nota_api, peso, avaliadores = Aluno.get_banca(self, api)
                    notas.append(("API", nota_api, peso/100 if peso else 0,
                                "Avaliação Parcial Individual"))

                # Avaliação Final Individual (52)
                afi = Avaliacao2.objects.filter(alocacao=alocacao,
                                                exame=Exame.objects.get(sigla="AFI"))

                if afi:
                    nota_afi, peso, avaliadores = Aluno.get_banca(self, afi)
                    notas.append(("AFI", nota_afi, peso/100 if peso else 0,
                                "Avaliação Final Individual"))

                # Avaliação Parcial de Grupo (53)
                apg = Avaliacao2.objects.filter(projeto=alocacao.projeto,
                                                exame=Exame.objects.get(sigla="APG"))

                if apg:
                    nota_apg, peso, avaliadores = Aluno.get_banca(self, apg)
                    notas.append(("APG", nota_apg, peso/100 if peso else 0,
                                "Avaliação Parcial de Grupo"))

                # Avaliação Final de Grupo (54)
                afg = Avaliacao2.objects.filter(projeto=alocacao.projeto,
                                                exame=Exame.objects.get(sigla="AFG"))

                if afg:
                    nota_afg, peso, avaliadores = Aluno.get_banca(self, afg)
                    notas.append(("AFG", nota_afg, peso/100 if peso else 0,
                                "Avaliação Final de Grupo"))
                    
            except Exame.DoesNotExist:
                raise ValidationError("<h2>Erro ao identificar tipos de avaliações!</h2>")

            edicao[str(alocacao.projeto.ano)+"."+str(alocacao.projeto.semestre)] = notas

        return edicao

    @property
    def get_medias(self):
        """Retorna médias."""
        medias = {}  # dicionário para cada alocação do estudante

        edicoes = self.get_notas

        for ano_semestre, edicao in edicoes.items():
            nota_final = 0
            peso_final = 0
            # for aval, nota, peso in edicao:
            for _, nota, peso, _ in edicao:
                peso_final += peso
                nota_final += nota * peso
            peso_final = round(peso_final, 2)
            medias[ano_semestre] = {"media": nota_final, "pesos": peso_final}

        alocacoes = Alocacao.objects.filter(aluno=self.pk)
        for alocacao in alocacoes:
            reprovacao = Reprovacao.objects.filter(alocacao=alocacao)
            if reprovacao:
                ano_semestre = str(alocacao.projeto.ano) + "." + str(alocacao.projeto.semestre)
                medias[ano_semestre] = {
                    "media": reprovacao.last().nota,
                    "pesos": 1
                }

        return medias


    @property
    def get_alocacoes(self):
        """Retorna alocações do estudante."""
        alocacoes = {}  # dicionário para cada alocação do estudante

        todas_alocacao = Alocacao.objects.filter(aluno=self.pk)

        for alocacao in todas_alocacao:
            ano_semestre = str(alocacao.projeto.ano) + "." + str(alocacao.projeto.semestre)
            alocacoes[ano_semestre] = alocacao

        return alocacoes

    # APARENTEMENTE NÃO MAIS SENDO USADO
    # @property
    # def get_peso(self):
    #     """Retorna soma dos pesos das notas."""
    #     peso_final = 0
    #     for _, _, peso, _ in self.get_notas:
    #         peso_final += peso
    #     return peso_final

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
        if self.proposta and self.proposta.titulo:
            mensagem += self.proposta.titulo
        return mensagem


class Alocacao(models.Model):
    """Projeto em que o aluno está alocado."""

    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE)
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE)

    avaliacao_intermediaria = models.DateTimeField("Avaliação Intermediária", default=None, blank=True, null=True,
                                                   help_text="Momento em que o orientador verificou a avaliação intermediária de par do estudante")
    
    avaliacao_final = models.DateTimeField("Avaliação Final", default=None, blank=True, null=True,
                                            help_text="Momento em que o orientador verificou a avaliação final de par do estudante")
    

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

    @property
    def get_notas(self):
        """Retorna notas do estudante no projeto."""
        edicoes = self.aluno.get_notas
        return edicoes[str(self.projeto.ano)+"."+str(self.projeto.semestre)]

    @property
    def get_media(self):
        """Retorna média e peso final."""
        reprovacao = Reprovacao.objects.filter(alocacao=self)
        if reprovacao:
            return {"media": reprovacao.last().nota, "pesos": 1}

        edicao = self.get_notas

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


class Parceiro(models.Model):  # da empresa (não do Insper)
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
                                           help_text="Nome para assinatura do coordenador do PFE")

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
