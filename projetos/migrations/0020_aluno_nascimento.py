# Generated by Django 2.1.7 on 2019-03-23 01:29

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('projetos', '0019_remove_aluno_nascimento'),
    ]

    operations = [
        migrations.AddField(
            model_name='aluno',
            name='nascimento',
            field=models.DateField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
