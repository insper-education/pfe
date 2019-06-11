# Desenvolvido para o Projeto Final de Engenharia
# Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
# Data: 15 de Maio de 2019

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MinValueValidator, MaxValueValidator

from projetos.models import Projeto

class PFEUser(AbstractUser):
    #username
    #first_name
    #last_name
    #email
    #is_active
    # add additional fields in here
    TIPO_DE_USUARIO_CHOICES = (
      (1, 'aluno'),
      (2, 'professor'),
      (3, 'funcionario'),
      (4, 'administrador'),
    )
    tipo_de_usuario = models.PositiveSmallIntegerField(choices=TIPO_DE_USUARIO_CHOICES, default=4)

    def __str__(self):
        return self.username

class Professor(models.Model):
    #login = models.CharField(primary_key=True, max_length=20)
    user = models.OneToOneField(PFEUser, on_delete=models.CASCADE)
    #nome = models.CharField(max_length=80)
    #email = models.EmailField(null=True, blank=True)
    class Meta:
        ordering = ['user']
        permissions = (("altera_professor", "Professor altera valores"), )
    def __str__(self):
        return self.user.username

class Aluno(models.Model):
    TIPOS_CURSO = (
        ('C', 'Computação'),
        ('M', 'Mecânica'),
        ('X', 'Mecatrônica'),
    )
    user = models.OneToOneField(PFEUser, on_delete=models.CASCADE)
    #bio = models.TextField(max_length=500, blank=True)    
    curso = models.CharField(max_length=1, choices=TIPOS_CURSO, help_text='Curso Matriculado',)
    opcoes = models.ManyToManyField(Projeto, through='Opcao', help_text='Opcoes de projeto escolhidos')
    nascimento = models.DateField(null=True, blank=True, help_text='Data de nascimento')
    local_de_origem = models.CharField(max_length=30, blank=True, help_text='Local de nascimento')
    email_pessoal = models.EmailField(null=True, blank=True, help_text='e-mail pessoal')
    anoPFE = models.PositiveIntegerField(null=True, blank=True, validators=[MinValueValidator(2018),MaxValueValidator(3018)], help_text='Ano que cursará o PFE')
    semestrePFE = models.PositiveIntegerField(null=True, blank=True, validators=[MinValueValidator(1),MaxValueValidator(2)], help_text='Semestre que cursará o PFE')

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

    # def __str__(self):
    #     return   ("V" if self.inovacao_social else "F") + " "\
    #            + ("V" if self.ciencia_dos_dados else "F") + " "\
    #            + ("V" if self.modelagem_3D else "F") + " "\
    #            + ("V" if self.manufatura else "F") + " "\
    #            + ("V" if self.resistencia_dos_materiais else "F") + " "\
    #            + ("V" if self.modelagem_de_sistemas else "F") + " "\
    #            + ("V" if self.controle_e_automacao else "F") + " "\
    #            + ("V" if self.termodinamica else "F") + " "\
    #            + ("V" if self.fluidodinamica else "F") + " "\
    #            + ("V" if self.eletronica_digital else "F") + " "\
    #            + ("V" if self.programacao else "F") + " "\
    #            + ("V" if self.inteligencia_artificial else "F") + " "\
    #            + ("V" if self.computacao_em_nuvem else "F") + " "\
    #            + ("V" if self.visao_computacional else "F") + " "\
    #            + ("V" if self.computacao_de_alto_desempenho else "F") + " "\
    #            + ("V" if self.robotica else "F") + " "\
    #            + ("V" if self.realidade_virtual_aumentada else "F") + " "\
    #            + ("V" if self.protocolos_de_comunicacao else "F") + " "\
    #            + ("V" if self.eficiencia_energetica else "F") + " "\
    #            + ("V" if self.administracao_economia_financas else "F")

    class Meta:
        ordering = ['user']
        permissions = (("altera_professor", "Professor altera valores"), )
    def __str__(self):
        return self.user.username


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
    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE)
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE)
    #razao = models.CharField(max_length=200)
    #prioridade = models.PositiveSmallIntegerField(default=0)
    prioridade = models.PositiveSmallIntegerField()
    class Meta:
        ordering = ['prioridade']
        permissions = (("altera_professor", "Professor altera valores"), )
    def __str__(self):
        return self.aluno.user.username+" >>> "+self.projeto.titulo

class Funcionario(models.Model):  # da empresa (não do Insper)
    user = models.OneToOneField(PFEUser, on_delete=models.CASCADE)
    #login = models.CharField(primary_key=True, max_length=20)
    #nome = models.CharField(max_length=80)
    #empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    #email = models.EmailField(null=True, blank=True)
    #gestor_responsavel = models.EmailField()
    #mentor_tecnico = models.EmailField()
    #recursos_humanos = models.EmailField()
    class Meta:
        ordering = ['user']
        permissions = (("altera_empresa", "Empresa altera valores"), ("altera_professor", "Professor altera valores"), )

    def __str__(self):
        return self.user.username

class Administrador(models.Model):
    user = models.OneToOneField(PFEUser, on_delete=models.CASCADE)
    class Meta:
        ordering = ['user']
        permissions = (("altera_empresa", "Empresa altera valores"), ("altera_professor", "Professor altera valores"), )
    def __str__(self):
        return self.user.username


@receiver(post_save, sender=PFEUser)
def create_user_aluno(sender, instance, created, **kwargs):
    if instance.tipo_de_usuario == 1 : #aluno
        Aluno.objects.get_or_create(user=instance)
    elif instance.tipo_de_usuario == 2 : #professor
        Professor.objects.get_or_create(user=instance)
    elif instance.tipo_de_usuario == 3 : #funcionario
        Funcionario.objects.get_or_create(user=instance)
    elif instance.tipo_de_usuario == 4 : #administrador
        Administrador.objects.get_or_create(user=instance)

      
@receiver(post_save, sender=PFEUser)
def save_user_aluno(sender, instance, **kwargs):
    if instance.tipo_de_usuario == 1 : #aluno
        instance.aluno.save()
    elif instance.tipo_de_usuario == 2 : #professor
        instance.professor.save()
    elif instance.tipo_de_usuario == 3 : #funcionario
        instance.funcionario.save()
    elif instance.tipo_de_usuario == 4 : #administrador
        instance.administrador.save()
