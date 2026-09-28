from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def migrar_status_para_workflow(apps, schema_editor):
    SolicitacaoReforco = apps.get_model('empenho', 'SolicitacaoReforco')
    SolicitacaoReforco.objects.filter(status__in=['ABERTA', 'CIENTE']).update(
        status='PENDENTE'
    )


class Migration(migrations.Migration):

    dependencies = [
        ('empenho', '0002_solicitacaoreforco'),
    ]

    operations = [
        migrations.RenameField(
            model_name='solicitacaoreforco',
            old_name='quantidade_solicitada',
            new_name='quantidade',
        ),
        migrations.AddField(
            model_name='solicitacaoreforco',
            name='justificativa',
            field=models.TextField(default=''),
            preserve_default=False,
        ),
        migrations.RunPython(
            migrar_status_para_workflow,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name='solicitacaoreforco',
            name='status',
            field=models.CharField(
                choices=[
                    ('PENDENTE', 'Pendente'),
                    ('ATENDIDA', 'Atendida'),
                    ('RECUSADA', 'Recusada'),
                ],
                default='PENDENTE',
                max_length=10,
            ),
        ),
        migrations.RemoveField(
            model_name='solicitacaoreforco',
            name='ciente_por',
        ),
        migrations.RemoveField(
            model_name='solicitacaoreforco',
            name='data_ciencia',
        ),
        migrations.AlterField(
            model_name='solicitacaoreforco',
            name='item_empenho',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='solicitacoes_reforco',
                to='empenho.itemempenho',
            ),
        ),
        migrations.AddField(
            model_name='solicitacaoreforco',
            name='respondida_por',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='solicitacoes_reforco_respondidas',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='solicitacaoreforco',
            name='resposta',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='solicitacaoreforco',
            name='operacao',
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='solicitacao_reforco',
                to='empenho.operacaoitem',
            ),
        ),
        migrations.AddField(
            model_name='solicitacaoreforco',
            name='data_resposta',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='solicitacaoreforco',
            name='vista_pelo_solicitante',
            field=models.BooleanField(default=True),
        ),
    ]
