# Generated for rubricas por evidências

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('academica', '0002_auto_20251007_0924'),
        ('projetos', '0002_auto_20251007_0924'),
        ('users', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='RubricaEvidenciaAvaliacao',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rubric_id', models.CharField(help_text='ID da rubrica configurada', max_length=80)),
                ('schema_version', models.CharField(help_text='Versão do schema da rubrica', max_length=32)),
                ('config_hash', models.CharField(blank=True, help_text='Hash do arquivo de configuração usado', max_length=64)),
                ('answers_json', models.TextField(blank=True, default='{}', help_text='Respostas selecionadas por nó')),
                ('path_json', models.TextField(blank=True, default='[]', help_text='Caminho percorrido no fluxo')),
                ('evidence_json', models.TextField(blank=True, default='[]', help_text='Evidências registradas')),
                ('dimension_results_json', models.TextField(blank=True, default='[]', help_text='Resultados por dimensão')),
                ('applied_caps_json', models.TextField(blank=True, default='[]', help_text='Limites aplicados')),
                ('warnings_json', models.TextField(blank=True, default='[]', help_text='Alertas gerados')),
                ('rationale_json', models.TextField(blank=True, default='[]', help_text='Racional determinístico da recomendação')),
                ('recommended_grade', models.CharField(blank=True, help_text='Menção recomendada originalmente', max_length=16)),
                ('final_grade', models.CharField(blank=True, help_text='Menção final escolhida pelo professor', max_length=16)),
                ('override_reason', models.TextField(blank=True, help_text='Justificativa quando a menção final difere da recomendação')),
                ('status', models.CharField(choices=[('draft', 'Rascunho'), ('confirmed', 'Confirmada')], default='draft', max_length=16)),
                ('confirmed_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('alocacao', models.ForeignKey(blank=True, help_text='Alocação avaliada, quando aplicável', null=True, on_delete=django.db.models.deletion.SET_NULL, to='users.Alocacao')),
                ('avaliador', models.ForeignKey(blank=True, help_text='Professor avaliador', null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('banca', models.ForeignKey(blank=True, help_text='Banca avaliada pelo fluxo assistido', null=True, on_delete=django.db.models.deletion.SET_NULL, to='projetos.Banca')),
                ('exame', models.ForeignKey(blank=True, help_text='Exame associado à avaliação', null=True, on_delete=django.db.models.deletion.SET_NULL, to='academica.Exame')),
                ('objetivo', models.ForeignKey(blank=True, help_text='Objetivo de aprendizagem associado à rubrica', null=True, on_delete=django.db.models.deletion.SET_NULL, to='projetos.ObjetivosDeAprendizagem')),
                ('projeto', models.ForeignKey(blank=True, help_text='Projeto avaliado', null=True, on_delete=django.db.models.deletion.SET_NULL, to='projetos.Projeto')),
            ],
            options={
                'verbose_name': 'Rubrica por Evidências',
                'verbose_name_plural': 'Rubricas por Evidências',
                'ordering': ['-updated_at'],
            },
        ),
    ]
