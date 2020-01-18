#!/usr/bin/env python
#pylint: disable=unused-argument
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Maio de 2019
"""

from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.functional import curry

from projetos.models import Projeto, Empresa

####   PARA PORTAR AS AREAS DE INTERESSE DE ALUNOS PARA CÁ, E USAR NO PROEJETO  #####
#areas de interesse
class Areas(models.Model):
    """Áreas de interesse dos projetos de engenharia."""
    inovacao_social = models.BooleanField(default=False)
    ciencia_dos_dados = models.BooleanField(default=False)
    modelagem_3D = models.BooleanField(default=False)
    manufatura = models.BooleanField(default=False)
    resistencia_dos_materiais = models.BooleanField(default=False)
    modelagem_de_sistemas = models.BooleanField(default=False)
    controle_e_automacao = models.BooleanField(default=False)
    termodinamica = models.BooleanField(default=False)
    fluidodinamica = models.BooleanField(default=False)
    eletronica_digital = models.BooleanField(default=False)
    programacao = models.BooleanField(default=False)
    inteligencia_artificial = models.BooleanField(default=False)
    banco_de_dados = models.BooleanField(default=False)
    computacao_em_nuvem = models.BooleanField(default=False)
    visao_computacional = models.BooleanField(default=False)
    computacao_de_alto_desempenho = models.BooleanField(default=False)
    robotica = models.BooleanField(default=False)
    realidade_virtual_aumentada = models.BooleanField(default=False)
    protocolos_de_comunicacao = models.BooleanField(default=False)
    eficiencia_energetica = models.BooleanField(default=False)
    administracao_economia_financas = models.BooleanField(default=False)

    def __str__(self):
        return   ("V" if self.inovacao_social else "F") + " "\
               + ("V" if self.ciencia_dos_dados else "F") + " "\
               + ("V" if self.modelagem_3D else "F") + " "\
               + ("V" if self.manufatura else "F") + " "\
               + ("V" if self.resistencia_dos_materiais else "F") + " "\
               + ("V" if self.modelagem_de_sistemas else "F") + " "\
               + ("V" if self.controle_e_automacao else "F") + " "\
               + ("V" if self.termodinamica else "F") + " "\
               + ("V" if self.fluidodinamica else "F") + " "\
               + ("V" if self.eletronica_digital else "F") + " "\
               + ("V" if self.programacao else "F") + " "\
               + ("V" if self.inteligencia_artificial else "F") + " "\
               + ("V" if self.computacao_em_nuvem else "F") + " "\
               + ("V" if self.visao_computacional else "F") + " "\
               + ("V" if self.computacao_de_alto_desempenho else "F") + " "\
               + ("V" if self.robotica else "F") + " "\
               + ("V" if self.realidade_virtual_aumentada else "F") + " "\
               + ("V" if self.protocolos_de_comunicacao else "F") + " "\
               + ("V" if self.eficiencia_energetica else "F") + " "\
               + ("V" if self.administracao_economia_financas else "F")

class PFEUser(AbstractUser):
    """Classe base para todos os usuários do PFE (Alunos, Professores, Parceiros)."""
    # Atualizar para AbstractBaseUser que permite colocar mais caracteres nos campos
    #username
    #first_name
    #last_name
    #email
    #is_active
    # add additional fields in here
    TIPO_DE_USUARIO_CHOICES = (
        (1, 'aluno'),
        (2, 'professor'),
        (3, 'parceiro'),
        (4, 'administrador'),
    )
    tipo_de_usuario = models.PositiveSmallIntegerField(choices=TIPO_DE_USUARIO_CHOICES, default=1,
                                                       help_text='cada usuário tem um perfil único')
    cpf = models.CharField(max_length=11, null=True, blank=True,
                           help_text='CPF do usuário')
    membro_comite = \
        models.BooleanField(default=False, help_text='caso membro do comitê do PFE')
    def __str__(self):
        return self.first_name + " " + self.last_name + \
            " (" + self.TIPO_DE_USUARIO_CHOICES[self.tipo_de_usuario-1][1] + ")"
        #return self.username #ver se atualizar isso para first_name não quebra o projeto

class Professor(models.Model):
    """Classe de usuários com estatus de Professor."""
    user = models.OneToOneField(PFEUser, related_name='professor', on_delete=models.CASCADE)
    areas = models.TextField(max_length=500, blank=True)
    website = models.URLField(max_length=250, null=True, blank=True)
    lattes = models.URLField(max_length=250, null=True, blank=True)

    class Meta:
        ordering = ['user']
        permissions = (("altera_professor", "Professor altera valores"), )
    def __str__(self):
        return self.user.first_name+" "+self.user.last_name

class Aluno(models.Model):
    """Classe de usuários com estatus de Aluno."""
    TIPOS_CURSO = (
        ('C', 'Computação'),
        ('M', 'Mecânica'),
        ('X', 'Mecatrônica'),
    )
    user = models.OneToOneField(PFEUser, related_name='aluno', on_delete=models.CASCADE)
    matricula = models.CharField(max_length=8, null=True, blank=True,
                                 help_text='Número de matrícula')
    #bio = models.TextField(max_length=500, blank=True)
    curso = models.CharField(max_length=1, choices=TIPOS_CURSO,
                             help_text='Curso Matriculado',)
    opcoes = models.ManyToManyField(Projeto, through='Opcao',
                                    help_text='Opcoes de projeto escolhidos')
    nascimento = models.DateField(null=True, blank=True,
                                  help_text='Data de nascimento')
    local_de_origem = models.CharField(max_length=30, blank=True,
                                       help_text='Local de nascimento')
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
    #alocado = models.ForeignKey(Projeto, null=True, blank=True, on_delete=models.SET_NULL,
    #                            related_name='aluno_alocado', help_text='projeto selecionado')

    #areas de interesse
    inovacao_social = models.BooleanField(default=False)
    ciencia_dos_dados = models.BooleanField(default=False)
    modelagem_3D = models.BooleanField(default=False)
    manufatura = models.BooleanField(default=False)
    resistencia_dos_materiais = models.BooleanField(default=False)
    modelagem_de_sistemas = models.BooleanField(default=False)
    controle_e_automacao = models.BooleanField(default=False)
    termodinamica = models.BooleanField(default=False)
    fluidodinamica = models.BooleanField(default=False)
    eletronica_digital = models.BooleanField(default=False)
    programacao = models.BooleanField(default=False)
    inteligencia_artificial = models.BooleanField(default=False)
    banco_de_dados = models.BooleanField(default=False)
    computacao_em_nuvem = models.BooleanField(default=False)
    visao_computacional = models.BooleanField(default=False)
    computacao_de_alto_desempenho = models.BooleanField(default=False)
    robotica = models.BooleanField(default=False)
    realidade_virtual_aumentada = models.BooleanField(default=False)
    protocolos_de_comunicacao = models.BooleanField(default=False)
    eficiencia_energetica = models.BooleanField(default=False)
    administracao_economia_financas = models.BooleanField(default=False)

    #### REMOVER AS AREAS DO CORPO DO ALUNO  ######
    #areas = models.ForeignKey(Areas, on_delete=models.CASCADE)
    #areas = models.OneToOneField(Areas, on_delete=models.CASCADE)
    #areas = models.OneToOneField(Areas, null=True, blank=True, on_delete=models.CASCADE)

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
            curried_method = curry(self._get_help_text, field_name=field.name)

            # And we add this method to the instance of the class.
            setattr(self, method_name, curried_method)

    class Meta:
        ordering = ['user']
        permissions = ()
    def __str__(self):
        #return self.user.username
        return self.user.get_full_name()

    # def opcao(self,i):
    #     try:
    #         valor = self.opcoes.all()[i]
    #     except IndexError:
    #         valor = 'vazio'
    #     return valor
    # def opcao1(self):
    #     return self.opcao(0)
    # def opcao2(self):
    #     return self.opcao(1)
    # def opcao3(self):
    #     return self.opcao(2)
    # def opcao4(self):
    #     return self.opcao(3)
    # def opcao5(self):
    #     return self.opcao(4)
    # opcao1.short_description = 'Opcao 1'
    # opcao2.short_description = 'Opcao 2'
    # opcao3.short_description = 'Opcao 3'
    # opcao4.short_description = 'Opcao 4'
    # opcao5.short_description = 'Opcao 5'

class Opcao(models.Model):
    """Opções de Projetos pelos Alunos com suas prioridades."""
    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE)
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE)
    #razao = models.CharField(max_length=200)
    prioridade = models.PositiveSmallIntegerField()
    class Meta:
        ordering = ['prioridade']
        permissions = (("altera_professor", "Professor altera valores"), )
    def __str__(self):
        return self.aluno.user.username+" >>> "+self.projeto.titulo

class Alocacao(models.Model):
    """Projeto em que o aluno está alocado."""
    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE)
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE)
    CONCEITOS = (
        (127, 'NA'),
        (10, 'A+'),
        (9, 'A'),
        (8, 'B+'),
        (7, 'B'),
        (6, 'C+'),
        (5, 'C'),
        (4, 'D'),
        (0, 'I'),
    )
    conceito = models.PositiveSmallIntegerField(choices=CONCEITOS, default=127)
    class Meta:
        permissions = (("altera_professor", "Professor altera valores"), )
        ordering = ['projeto__ano', 'projeto__semestre',]
    def __str__(self):
        return self.aluno.user.username+" >>> "+self.projeto.titulo

class Parceiro(models.Model):  # da empresa (não do Insper)
    """Classe de usuários com estatus de Parceiro (pessoal das organizações parceiras)."""
    user = models.OneToOneField(PFEUser, related_name='parceiro', on_delete=models.CASCADE)
    organizacao = models.ForeignKey(Empresa, null=True, blank=True, on_delete=models.CASCADE)
    cargo = models.CharField(max_length=50, blank=True, help_text='Cargo Funcional')
    telefone = models.CharField(max_length=20, blank=True, help_text='Telefone Fixo')
    celular = models.CharField(max_length=20, blank=True, help_text='Telefone Celular')
    skype = models.CharField(max_length=20, blank=True, help_text='Identificação Skype')
    #gestor_responsavel = models.BooleanField(default=False)
    #mentor_tecnico = models.BooleanField(default=False)
    #recursos_humanos = models.BooleanField(default=False)
    class Meta:
        ordering = ['user']
        permissions = (("altera_parceiro", "Parceiro altera valores"),)

    def __str__(self):
        return self.user.username

class Administrador(models.Model):
    """Classe de usuários com estatus de Administrador."""
    user = models.OneToOneField(PFEUser, related_name='administrador', on_delete=models.CASCADE)
    class Meta:
        ordering = ['user']
        permissions = (("altera_empresa", "Empresa altera valores"),
                       ("altera_professor", "Professor altera valores"), )
    def __str__(self):
        return self.user.username

@receiver(post_save, sender=PFEUser)
def create_user_dependency(sender, instance, created, **kwargs):
    """Quando um usuário do PFE é criado/salvo, seu corespondente específico também é criado."""
    if instance.tipo_de_usuario == 1: #aluno
        Aluno.objects.get_or_create(user=instance)
    elif instance.tipo_de_usuario == 2: #professor
        Professor.objects.get_or_create(user=instance)
    elif instance.tipo_de_usuario == 3: #Parceiro
        Parceiro.objects.get_or_create(user=instance)
    elif instance.tipo_de_usuario == 4: #administrador
        Administrador.objects.get_or_create(user=instance)

@receiver(post_save, sender=PFEUser)
def save_user_dependency(sender, instance, **kwargs):
    """Quando um usuário do PFE é criado/salvo, seu corespondente específico também é criado."""
    if instance.tipo_de_usuario == 1: #aluno
        instance.aluno.save()
    elif instance.tipo_de_usuario == 2: #professor
        instance.professor.save()
    elif instance.tipo_de_usuario == 3: #Parceiro
        instance.parceiro.save()
    elif instance.tipo_de_usuario == 4: #administrador
        instance.administrador.save()
