from django.contrib import admin
import django.contrib.admin.options as admin_opt

# Dos projetos
from .models import Projeto, Empresa, Banca, Disciplina, Cursada, Recomendada

# Das dinâmicas
from .models import Encontro, Evento

# Da coordenação
from .models import Configuracao, Aviso, Documento, Anotacao, Reembolso, Banco

# Do Insper
from .models import Entidade


# Função abaixo permite duplicar entradas no banco de dados
def dup_event(modeladmin:admin_opt.ModelAdmin, request, queryset):
    for object in queryset:
        from_id = object.id
        object.id = None
        if Configuracao.objects.all().first().semestre == 1:
            object.semestre = 2
            object.ano = Configuracao.objects.all().first().ano
        else:
            object.semestre = 1
            object.ano = Configuracao.objects.all().first().ano + 1
        object.save()
        message="duplicando de {} para {}".format(from_id, object.id)
        modeladmin.log_addition(request=request,object=object,message=message)
dup_event.short_description = "Duplicar Projeto(s)"

@admin.register(Projeto)
class ProjetoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'empresa', 'ano', 'semestre')
    fieldsets = (
        (None, {
            'fields': ('titulo', 'titulo_final', 'descricao', 'expectativas', 'areas', 'recursos', 
            'departamento',
            'anexo','imagem',
            'avancado', 'ano', 'semestre', 'disponivel', 
            'orientador',
            'perfil_aluno1_computacao', 'perfil_aluno1_mecanica', 'perfil_aluno1_mecatronica',
            'perfil_aluno2_computacao', 'perfil_aluno2_mecanica', 'perfil_aluno2_mecatronica',
            'perfil_aluno3_computacao', 'perfil_aluno3_mecanica', 'perfil_aluno3_mecatronica',
            'perfil_aluno4_computacao', 'perfil_aluno4_mecanica', 'perfil_aluno4_mecatronica',
             )
        }),
        ('Origem', {
            'fields': ('empresa',)
        }),
    )
    actions = [dup_event]


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('sigla', 'nome_empresa',)

@admin.register(Configuracao)
class ConfiguracaoAdmin(admin.ModelAdmin):
    list_display = ('ano', 'semestre',)

@admin.register(Disciplina)
class DisciplinaAdmin(admin.ModelAdmin):
    list_display = ('nome',)

@admin.register(Anotacao)
class AnotacaoAdmin(admin.ModelAdmin):
    list_display = ('data', 'organizacao', 'autor',)

@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = ('tipo_de_documento', 'organizacao', 'usuario', 'projeto')

# Lista de Bancos Brasileiros
@admin.register(Banco)
class BancoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'codigo')

# Pedidos de reembolso
@admin.register(Reembolso)
class ReembolsoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'data', 'valor')

# Informações das Bancas, como datas e membros
@admin.register(Banca)
class BancaAdmin(admin.ModelAdmin):
    list_display = ('projeto', 'get_orientador', 'get_organizacao', 'startDate')
    def get_orientador(self, obj):
        return obj.projeto.orientador
    get_orientador.short_description = 'Orientador'
    get_orientador.admin_order_field = 'projeto__orientador'
    def get_organizacao(self, obj):
        return obj.projeto.empresa
    get_organizacao.short_description = 'Organização'
    get_organizacao.admin_order_field = 'projeto__empresa'

# Avisos para a coordenação do PFE
@admin.register(Aviso)
class AvisoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'delta',)

admin.site.register(Cursada)
admin.site.register(Recomendada) 
admin.site.register(Evento) # Todos os eventos do PFE com suas datas
admin.site.register(Encontro) # Informações das Encontros (com os facilitadores)
admin.site.register(Entidade) # Para ser preenchido com as entidades estudantis
