#!/usr/bin/env python
#pylint: disable=unused-argument
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Maio de 2019
"""

from functools import partial

from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from projetos.models import Projeto, Proposta, Organizacao, Avaliacao2, ObjetivosDeAprendizagem


class PFEUser(AbstractUser):
    """Classe base para todos os usuários do PFE (Alunos, Professores, Parceiros)."""
    # Atualizar para AbstractBaseUser que permite colocar mais caracteres nos campos
    # username
    # first_name
    # last_name
    # email
    # is_active
    # add additional fields in here
    TIPO_DE_USUARIO_CHOICES = (
        (1, 'aluno'),
        (2, 'professor'),
        (3, 'parceiro'),
        (4, 'administrador'),
    )
    tipo_de_usuario = models.PositiveSmallIntegerField(choices=TIPO_DE_USUARIO_CHOICES, default=1,
                                                       help_text='cada usuário tem um perfil único')

    linkedin = models.URLField("LinkedIn", max_length=250, null=True, blank=True,
                               help_text='LinkedIn do usuário')

    membro_comite = \
        models.BooleanField(default=False, help_text='caso membro do comitê do PFE')

    GENERO_CHOICES = (
        ('X', 'Nao Informado'),
        ('M', 'Masculino'),
        ('F', 'Feminino'),
    )
    genero = models.CharField(max_length=1, choices=GENERO_CHOICES, default='X',
                              help_text='sexo do usuário')

    TIPO_LINGUA = (
        (1, 'português'),
        (2, 'inglês'),
    )
    tipo_lingua = models.PositiveSmallIntegerField(choices=TIPO_LINGUA, default=1,
                                                   help_text='língua usada para comunicação')

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        ordering = ['first_name', 'last_name']

    @classmethod
    def create(cls):
        """Cria um objeto (entrada) em PFEUser."""
        user = cls()
        return user

    def __str__(self):
        texto = self.first_name + " " + self.last_name
        if self.tipo_de_usuario == 1: # (1, 'aluno'),
            texto += " (estudante"
            if self.aluno.anoPFE and self.aluno.semestrePFE:
                texto += " : " + str(self.aluno.anoPFE) + "." + str(self.aluno.semestrePFE)
        elif self.tipo_de_usuario == 2: #(2, 'professor'),
            texto += " (professor"
            if self.professor.dedicacao:
                texto += " : " + self.professor.dedicacao
        elif self.tipo_de_usuario == 3: #(3, 'parceiro'),
            texto += " (parceiro"
            if self.parceiro.organizacao and self.parceiro.organizacao.sigla:
                texto += " : " + self.parceiro.organizacao.sigla
        elif self.tipo_de_usuario == 4: #(4, 'administrador'),
            texto += " (professor : TI)"

        texto += ")"
        return texto

class Professor(models.Model):
    """Classe de usuários com estatus de Professor."""
    user = models.OneToOneField(PFEUser, related_name='professor', on_delete=models.CASCADE)

    TIPO_DEDICACAO = (
        ("TI", "Tempo Integral"),
        ("TP", 'Tempo Parcial'),
    )

    dedicacao = models.CharField("Dedicação", max_length=2,
                                 choices=TIPO_DEDICACAO, null=True, blank=True,
                                 help_text='Tipo de dedicação do professor')

    areas = models.TextField(max_length=500, null=True, blank=True,
                             help_text='Áreas de Interesse do Professor')
    website = models.URLField(max_length=75, null=True, blank=True,
                              help_text='Website profissional do Professor')
    lattes = models.URLField(max_length=75, null=True, blank=True,
                             help_text='Link para o currículo Lattes do Professor')

    class Meta:
        verbose_name = 'Professor'
        verbose_name_plural = 'Professores'
        ordering = ['user']
        permissions = (("altera_professor", "Professor altera valores"), )

    def __str__(self):
        return self.user.first_name+" "+self.user.last_name

    @classmethod
    def create(cls, usuario):
        """Cria um Professor e já associa o usuário."""
        professor = cls(user=usuario)
        return professor


class Aluno(models.Model):
    """Classe de usuários com estatus de Aluno."""
    TIPOS_CURSO = (
        ('C', 'Computação'),
        ('M', 'Mecânica'),
        ('X', 'Mecatrônica'),
    )
    user = models.OneToOneField(PFEUser, related_name='aluno', on_delete=models.CASCADE)
    matricula = models.CharField("Matrícula", max_length=8, null=True, blank=True,
                                 help_text='Número de matrícula')
    curso = models.CharField(max_length=1, choices=TIPOS_CURSO,
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
                                 help_text='Trabalhou ou estagio em alguma empresa de engenharia?')
    social = models.TextField(max_length=1000, null=True, blank=True,
                              help_text='Já participou de atividade sociais?')
    entidade = models.TextField(max_length=1000, null=True, blank=True,
                                help_text='Já participou de alguma entidade estudantil do Insper?')
    familia = models.TextField(max_length=1000, null=True, blank=True,\
              help_text='Possui familiares em empresa que está aplicando? Ou empresa concorrente?')

    #https://bradmontgomery.net/blog/django-hack-help-text-modal-instance/
    def _get_help_text(self, field_name):
        """Given a field name, return it's help text."""
        for field in self._meta.fields:
            if field.name == field_name:
                return field.help_text

    def __init__(self, *args, **kwargs):
        # Call the superclass first; it'll create all of the field objects.
        super(Aluno, self).__init__(*args, **kwargs)

        # Again, iterate over all of our field objects.
        for field in self._meta.fields:
            # Create a string, get_FIELDNAME_help text
            method_name = "get_{0}_help_text".format(field.name)

            # We can use curry to create the method with a pre-defined argument
            curried_method = partial(self._get_help_text, field_name=field.name)

            # And we add this method to the instance of the class.
            setattr(self, method_name, curried_method)

    def get_curso(self):
        """Retorna em string o nome do curso."""
        for entry in Aluno.TIPOS_CURSO:
            if self.curso == entry[0]:
                return entry[1]
        return "Sem curso"

    def get_curso_completo(self):
        """Retorna em string com o nome completo do curso."""
        if self.curso == "C":
            return "Engenharia de Computação"
        if self.curso == "M":
            return "Engenharia Mecânica"
        if self.curso == "X":
            return "Engenharia Mecatrônica"
        return "Sem curso"


    def get_objetivos(self, avaliacoes_banca):
        """Retorna objetivos."""
        lista_objetivos = {}
        objetivos = ObjetivosDeAprendizagem.objects.all()
        for objetivo in objetivos:
            bancas = avaliacoes_banca.filter(objetivo=objetivo).\
                                                order_by('avaliador', '-momento')
            if bancas:
                lista_objetivos[objetivo] = {}
            for banca in bancas:
                # Se não for o mesmo avaliador
                if banca.avaliador not in lista_objetivos[objetivo]:
                    if banca.na:
                        lista_objetivos[objetivo][banca.avaliador] = None
                    else:
                        lista_objetivos[objetivo][banca.avaliador] = (float(banca.nota),
                                                                      float(banca.peso))
                # Senão é só uma avaliação de objetivo mais antiga

        if not lista_objetivos:
            return 0, None

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
                    val_objetivos[obj] = (val/count, pes/count)

        return val_objetivos, pes_total

    def get_banca(self, avaliacoes_banca):
        """Retorna média."""
        
        val_objetivos, pes_total  = Aluno.get_objetivos(self, avaliacoes_banca)

        if not val_objetivos:
            return 0, None

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

        return val, pes


    @property
    def get_edicoes(self):
        """Recuper as notas do Estudante."""
        edicao = {} # dicionário para cada alocação do estudante (por exemplo DP, ou PFE Avançado)

        alocacoes = Alocacao.objects.filter(aluno=self.pk)
        #supondo só uma alocação para agora
        #alocacao = alocacoes.first()

        for alocacao in alocacoes:

            notas = [] # iniciando uma lista de notas vazia

            # Banca Intermediária (1, 'intermediaria')
            avaliacoes_banca_interm = Avaliacao2.objects.filter(projeto=alocacao.projeto,
                                                                tipo_de_avaliacao=1)
            if avaliacoes_banca_interm:
                nota_banca_interm, peso = Aluno.get_objetivos(self, avaliacoes_banca_interm)
                print(nota_banca_interm)
                notas.append(("BI", nota_banca_interm, peso/100))

            # Banca Final (2, 'final')
            avaliacoes_banca_final = Avaliacao2.objects.filter(projeto=alocacao.projeto,
                                                               tipo_de_avaliacao=2)
            if avaliacoes_banca_final:
                nota_banca_final, peso = Aluno.get_objetivos(self, avaliacoes_banca_final)
                notas.append(("BF", nota_banca_final, peso/100))

            # Relatório de Planejamento (10, 'Relatório de Planejamento')
            relp = Avaliacao2.objects.filter(projeto=alocacao.projeto, tipo_de_avaliacao=10).\
                                      order_by('momento').last()
            if relp:
                notas.append(("RP", float(relp.nota), relp.peso/100))

            # Relatório Intermediário de Grupo (11, 'Relatório Intermediário de Grupo'),
            rig = Avaliacao2.objects.filter(projeto=alocacao.projeto, tipo_de_avaliacao=11)
            if rig:
                nota_rig, peso = Aluno.get_objetivos(self, rig)
                notas.append(("RIG", nota_rig, peso/100))

            # Relatório Final de Grupo (12, 'Relatório Final de Grupo'),
            rfg = Avaliacao2.objects.filter(projeto=alocacao.projeto, tipo_de_avaliacao=12)
            if rfg:
                nota_rfg, peso = Aluno.get_objetivos(self, rfg)
                notas.append(("RFG", nota_rfg, peso/100))

            # Relatório Intermediário Individual (21, 'Relatório Intermediário Individual'),
            rii = Avaliacao2.objects.filter(alocacao=alocacao, tipo_de_avaliacao=21)
            if rii:
                nota_rii, peso = Aluno.get_objetivos(self, rii)
                notas.append(("RII", nota_rii, peso/100))

            # Relatório Final Individual (22, 'Relatório Final Individual'),
            rfi = Avaliacao2.objects.filter(alocacao=alocacao, tipo_de_avaliacao=22)
            if rfi:
                nota_rfi, peso = Aluno.get_objetivos(self, rfi)
                notas.append(("RFI", nota_rfi, peso/100))

            ### NÃO MAIS USADAS, FORAM USADAS QUANDO AINDA EM DOIS SEMESTRES
            # Planejamento Primeira Fase  (50, 'Planejamento Primeira Fase')
            ppf = Avaliacao2.objects.filter(projeto=alocacao.projeto, tipo_de_avaliacao=50).\
                                     order_by('momento').last()
            if ppf:
                notas.append( ("PPF", float(ppf.nota), ppf.peso/100) )

            # Avaliação Parcial Individual (51, 'Avaliação Parcial Individual'),
            api = Avaliacao2.objects.filter(alocacao=alocacao, tipo_de_avaliacao=51)
            if api:
                nota_api, peso = Aluno.get_objetivos(self, api)
                notas.append(("API", nota_api, peso/100))

            # Avaliação Final Individual (52, 'Avaliação Final Individual'),
            afi = Avaliacao2.objects.filter(alocacao=alocacao, tipo_de_avaliacao=52)
            if afi:
                nota_afi, peso = Aluno.get_objetivos(self, afi)
                notas.append(("AFI", nota_afi, peso/100))

            edicao[str(alocacao.projeto.ano)+"."+str(alocacao.projeto.semestre)] = notas

        return edicao





    @property
    def get_notas(self):
        """Recuper as notas do Estudante."""
        edicao = {} # dicionário para cada alocação do estudante (por exemplo DP, ou PFE Avançado)

        alocacoes = Alocacao.objects.filter(aluno=self.pk)
        #supondo só uma alocação para agora
        #alocacao = alocacoes.first()

        for alocacao in alocacoes:

            notas = [] # iniciando uma lista de notas vazia

            # Banca Intermediária (1, 'intermediaria')
            avaliacoes_banca_interm = Avaliacao2.objects.filter(projeto=alocacao.projeto,
                                                                tipo_de_avaliacao=1)
            if avaliacoes_banca_interm:
                nota_banca_interm, peso = Aluno.get_banca(self, avaliacoes_banca_interm)
                notas.append( ("BI", nota_banca_interm, peso/100) )

            # Banca Final (2, 'final')
            avaliacoes_banca_final = Avaliacao2.objects.filter(projeto=alocacao.projeto,
                                                               tipo_de_avaliacao=2)
            if avaliacoes_banca_final:
                nota_banca_final, peso = Aluno.get_banca(self, avaliacoes_banca_final)
                notas.append(("BF", nota_banca_final, peso/100))

            # Relatório de Planejamento (10, 'Relatório de Planejamento')
            relp = Avaliacao2.objects.filter(projeto=alocacao.projeto, tipo_de_avaliacao=10).\
                                      order_by('momento').last()
            if relp:
                notas.append(("RP", float(relp.nota), relp.peso/100))

            # Relatório Intermediário de Grupo (11, 'Relatório Intermediário de Grupo'),
            rig = Avaliacao2.objects.filter(projeto=alocacao.projeto, tipo_de_avaliacao=11)
            if rig:
                nota_rig, peso = Aluno.get_banca(self, rig)
                notas.append(("RIG", nota_rig, peso/100))

            # Relatório Final de Grupo (12, 'Relatório Final de Grupo'),
            rfg = Avaliacao2.objects.filter(projeto=alocacao.projeto, tipo_de_avaliacao=12)
            if rfg:
                nota_rfg, peso = Aluno.get_banca(self, rfg)
                notas.append(("RFG", nota_rfg, peso/100))

            # Relatório Intermediário Individual (21, 'Relatório Intermediário Individual'),
            rii = Avaliacao2.objects.filter(alocacao=alocacao, tipo_de_avaliacao=21)
            if rii:
                nota_rii, peso = Aluno.get_banca(self, rii)
                notas.append(("RII", nota_rii, peso/100))

            # Relatório Final Individual (22, 'Relatório Final Individual'),
            rfi = Avaliacao2.objects.filter(alocacao=alocacao, tipo_de_avaliacao=22)
            if rfi:
                nota_rfi, peso = Aluno.get_banca(self, rfi)
                notas.append(("RFI", nota_rfi, peso/100))

            ### NÃO MAIS USADAS, FORAM USADAS QUANDO AINDA EM DOIS SEMESTRES
            # Planejamento Primeira Fase  (50, 'Planejamento Primeira Fase')
            ppf = Avaliacao2.objects.filter(projeto=alocacao.projeto, tipo_de_avaliacao=50).\
                                     order_by('momento').last()
            if ppf:
                notas.append( ("PPF", float(ppf.nota), ppf.peso/100) )

            # Avaliação Parcial Individual (51, 'Avaliação Parcial Individual'),
            api = Avaliacao2.objects.filter(alocacao=alocacao, tipo_de_avaliacao=51)
            if api:
                nota_api, peso = Aluno.get_banca(self, api)
                notas.append(("API", nota_api, peso/100))

            # Avaliação Final Individual (52, 'Avaliação Final Individual'),
            afi = Avaliacao2.objects.filter(alocacao=alocacao, tipo_de_avaliacao=52)
            if afi:
                nota_afi, peso = Aluno.get_banca(self, afi)
                notas.append(("AFI", nota_afi, peso/100))

            edicao[str(alocacao.projeto.ano)+"."+str(alocacao.projeto.semestre)] = notas

        return edicao

    @property
    def get_medias(self):
        """Retorna médias."""
        medias = {}  # dicionário para cada alocação do estudante (por exemplo DP, ou PFE Avançado)

        edicoes = self.get_notas

        for ano_semestre,edicao in edicoes.items():
            nota_final = 0
            peso_final = 0
            # for aval, nota, peso in edicao:
            for _, nota, peso in edicao:
                peso_final += peso
                nota_final += nota * peso
            peso_final = round(peso_final, 1)
            medias[ano_semestre] = {"media": nota_final, "pesos": peso_final}

        return medias

    @property
    def get_peso(self):
        """Retorna soma dos pesos das notas."""
        peso_final = 0
        for _, _, peso in self.get_notas:
            peso_final += peso
        return peso_final

    class Meta:
        ordering = ['user']
        permissions = ()
    def __str__(self):
        return self.user.get_full_name()

    @classmethod
    def create(cls, usuario):
        """Cria um Estudante e já associa o usuário."""
        estudante = cls(user=usuario)
        return estudante

class Opcao(models.Model):
    """Opções de Projetos pelos Alunos com suas prioridades."""
    proposta = models.ForeignKey(Proposta, null=True, blank=True, on_delete=models.SET_NULL)
    aluno = models.ForeignKey(Aluno, null=True, blank=True, on_delete=models.CASCADE)
    #razao = models.CharField(max_length=200)
    prioridade = models.PositiveSmallIntegerField()
    class Meta:
        verbose_name = 'Opção'
        verbose_name_plural = 'Opções'
        ordering = ['prioridade']
        permissions = (("altera_professor", "Professor altera valores"), )
    def __str__(self):
        return self.aluno.user.username + " >>> " + self.proposta.titulo

class Alocacao(models.Model):
    """Projeto em que o aluno está alocado."""
    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE)
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Alocação'
        verbose_name_plural = 'Alocações'
        permissions = (("altera_professor", "Professor altera valores"), )
        ordering = ['projeto__ano', 'projeto__semestre',]
    def __str__(self):
        return self.aluno.user.username+" >>> "+self.projeto.titulo

    @classmethod
    def create(cls, estudante, projeto):
        """Cria um Projeto (entrada) de Alocação."""
        alocacao = cls(projeto=projeto, aluno=estudante)
        return alocacao

    @property
    def get_edicoes(self):
        """Retorna objetivos."""
        edicoes = self.aluno.get_edicoes
        edicao = edicoes[str(self.projeto.ano)+"."+str(self.projeto.semestre)]
        return edicao

    @property
    def get_notas(self):
        """Retorna notas."""
        edicoes = self.aluno.get_notas
        edicao = edicoes[str(self.projeto.ano)+"."+str(self.projeto.semestre)]
        return edicao

    @property
    def get_media(self):
        """Retorna média e peso final."""
        edicao = self.get_notas

        nota_final = 0
        peso_final = 0
        # for aval, nota, peso in edicao:
        for _, nota, peso in edicao:
            peso_final += peso
            nota_final += nota * peso
        peso_final = round(peso_final, 1)
        
        return  {"media": nota_final, "pesos": peso_final}

    @property
    def media(self):
        """Retorna média final."""
        return self.get_media["media"]

    @property
    def peso(self):
        """Retorna peso final."""
        return self.get_media["pesos"]

    @property
    def get_notas(self):
        """Retorna notas do estudante no projeto."""
        edicoes = self.aluno.get_notas
        return edicoes[str(self.projeto.ano)+"."+str(self.projeto.semestre)]


class Parceiro(models.Model):  # da empresa (não do Insper)
    """Classe de usuários com estatus de Parceiro (pessoal das organizações parceiras)."""
    user = models.OneToOneField(PFEUser, related_name='parceiro', on_delete=models.CASCADE,
                                help_text='Identificaçãdo do usuário')
    organizacao = models.ForeignKey(Organizacao, on_delete=models.CASCADE,
                                    blank=True, null=True,
                                    help_text='Organização Parceira')
    cargo = models.CharField("Cargo", max_length=90, blank=True,
                             help_text='Cargo Funcional')
    telefone = models.CharField(max_length=20, blank=True,
                                help_text='Telefone Fixo')
    celular = models.CharField(max_length=20, blank=True,
                               help_text='Telefone Celular')
    skype = models.CharField(max_length=32, blank=True,
                             help_text='Identificação Skype')
    observacao = models.TextField("Observações", max_length=500, blank=True,
                                  help_text='Observações')

    principal_contato = models.BooleanField("Principal Contato", default=False)

    class Meta:
        ordering = ['user']
        permissions = (("altera_parceiro", "Parceiro altera valores"),)

    def __str__(self):
        if self.organizacao:
            return self.user.get_full_name()+" ["+self.organizacao.sigla+"]"
        else:
            return self.user.get_full_name()

    @classmethod
    def create(cls, usuario):
        """Cria um Parceiro e já associa o usuário."""
        parceiro = cls(user=usuario)
        return parceiro

class Administrador(models.Model):
    """Classe de usuários com estatus de Administrador."""
    user = models.OneToOneField(PFEUser, related_name='administrador', on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Administrador'
        verbose_name_plural = 'Administradores'
        ordering = ['user']
        permissions = (("altera_empresa", "Empresa altera valores"),
                       ("altera_professor", "Professor altera valores"), )
    def __str__(self):
        return self.user.username

    # @classmethod
    # def create(cls, usuario):
    #     """Cria um Administrador e já associa o usuário."""
    #     administrador = cls(user=usuario)
    #     return administrador
