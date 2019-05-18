from import_export import resources

from .models import Aluno

class AlunoResource(resources.ModelResource):
    class Meta:
        model = Aluno