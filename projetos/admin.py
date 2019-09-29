from django.contrib import admin

from .models import Projeto, Empresa, Configuracao
from .models import Disciplina, Cursada, Recomendada, Evento, Anotacao, Banca, Documento

@admin.register(Projeto)
class ProjetoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'empresa', 'ano', 'semestre')
    fieldsets = (
        (None, {
            'fields': ('titulo', 'descricao', 'expectativas', 
            'areas', 'recursos', 'imagem',
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

admin.site.register(Cursada)
admin.site.register(Recomendada) 
admin.site.register(Evento) # Todos os eventos do PFE com suas datas
admin.site.register(Banca) # Informações das Bancas, como datas e membros
