# Generated by Django 2.1.7 on 2019-03-23 00:49

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('projetos', '0016_auto_20190322_2105'),
    ]

    operations = [
        migrations.AddField(
            model_name='aluno',
            name='nascimento',
            field=models.DateTimeField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
