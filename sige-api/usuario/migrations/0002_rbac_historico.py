import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def converter_papeis(apps, schema_editor):
    Usuario = apps.get_model('usuario', 'Usuario')
    Usuario.objects.filter(papel='ADMIN').update(papel='DIRET')
    Usuario.objects.filter(papel='TECNI').update(papel='TECAD')


def reverter_papeis(apps, schema_editor):
    Usuario = apps.get_model('usuario', 'Usuario')
    Usuario.objects.filter(papel='DIRET').update(papel='ADMIN')
    Usuario.objects.filter(papel__in=['TECAD', 'NUTRI']).update(papel='TECNI')


class Migration(migrations.Migration):

    dependencies = [
        ('usuario', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(converter_papeis, reverter_papeis),
        migrations.AlterField(
            model_name='usuario',
            name='papel',
            field=models.CharField(
                choices=[
                    ('DIRET', 'Diretor'),
                    ('TECAD', 'Técnico Administrativo'),
                    ('NUTRI', 'Nutricionista'),
                ],
                default='TECAD',
                max_length=5,
            ),
        ),
        migrations.CreateModel(
            name='HistoricoAuditoria',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('papel', models.CharField(blank=True, max_length=5)),
                ('acao', models.CharField(max_length=40)),
                ('recurso', models.CharField(max_length=50)),
                ('entidade', models.CharField(blank=True, max_length=100)),
                ('entidade_id', models.CharField(blank=True, max_length=100, null=True)),
                ('valores_anteriores', models.JSONField(blank=True, default=dict)),
                ('valores_novos', models.JSONField(blank=True, default=dict)),
                ('permitido', models.BooleanField(default=True)),
                ('detalhe', models.TextField(blank=True)),
                ('data_hora', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('usuario', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='eventos_auditoria', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Histórico de auditoria',
                'verbose_name_plural': 'Históricos de auditoria',
                'ordering': ['-data_hora', '-id'],
            },
        ),
    ]
