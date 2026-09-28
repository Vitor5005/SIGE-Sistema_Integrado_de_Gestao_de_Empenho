from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('empenho', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SolicitacaoReforco',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                ('quantidade_solicitada', models.DecimalField(decimal_places=2, max_digits=10)),
                (
                    'status',
                    models.CharField(
                        choices=[('ABERTA', 'Aberta'), ('CIENTE', 'Ciente')],
                        default='ABERTA',
                        max_length=10,
                    ),
                ),
                ('data_solicitacao', models.DateTimeField(auto_now_add=True)),
                ('data_ciencia', models.DateTimeField(blank=True, null=True)),
                (
                    'ciente_por',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='solicitacoes_reforco_cientes',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    'item_empenho',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='solicitacoes_reforco',
                        to='empenho.itemempenho',
                    ),
                ),
                (
                    'solicitante',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='solicitacoes_reforco',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'ordering': ['-data_solicitacao', '-id'],
            },
        ),
    ]
