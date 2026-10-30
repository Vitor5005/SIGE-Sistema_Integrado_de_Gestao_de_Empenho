import django.db.models.deletion
from django.db import migrations, models


BATCH_SIZE = 500


def migrar_estoque_legado(apps, schema_editor):
    Estoque = apps.get_model('estoque', 'Estoque')
    MovimentacaoEstoque = apps.get_model('estoque', 'MovimentacaoEstoque')
    LoteEstoque = apps.get_model('estoque', 'LoteEstoque')
    MovimentacaoLote = apps.get_model('estoque', 'MovimentacaoLote')

    lotes = []
    for estoque in Estoque.objects.all().iterator(chunk_size=BATCH_SIZE):
        lotes.append(
            LoteEstoque(
                estoque_id=estoque.id,
                numero_lote='LEGADO',
                data_validade=None,
                saldo_atual=estoque.saldo_atual,
                legado=True,
            )
        )
        if len(lotes) == BATCH_SIZE:
            LoteEstoque.objects.bulk_create(lotes, batch_size=BATCH_SIZE)
            lotes = []
    if lotes:
        LoteEstoque.objects.bulk_create(lotes, batch_size=BATCH_SIZE)

    lotes_por_estoque_id = dict(
        LoteEstoque.objects.filter(numero_lote='LEGADO').values_list('estoque_id', 'id')
    )
    alocacoes = []
    for movimento in MovimentacaoEstoque.objects.all().iterator(chunk_size=BATCH_SIZE):
        alocacoes.append(
            MovimentacaoLote(
                movimentacao_id=movimento.id,
                lote_id=lotes_por_estoque_id[movimento.estoque_id],
                quantidade=movimento.quantidade,
                saldo_lote_resultante=movimento.saldo_resultante,
            )
        )
        if len(alocacoes) == BATCH_SIZE:
            MovimentacaoLote.objects.bulk_create(alocacoes, batch_size=BATCH_SIZE)
            alocacoes = []
    if alocacoes:
        MovimentacaoLote.objects.bulk_create(alocacoes, batch_size=BATCH_SIZE)


def reverter_estoque_legado(apps, schema_editor):
    MovimentacaoLote = apps.get_model('estoque', 'MovimentacaoLote')
    LoteEstoque = apps.get_model('estoque', 'LoteEstoque')

    MovimentacaoLote.objects.all().delete()
    LoteEstoque.objects.all().delete()


def criar_triggers_movimentacao_lote(apps, schema_editor):
    if schema_editor.connection.vendor != 'mysql':
        return

    schema_editor.execute('DROP TRIGGER IF EXISTS trg_mov_lote_bloqueia_update')
    schema_editor.execute('DROP TRIGGER IF EXISTS trg_mov_lote_bloqueia_delete')
    schema_editor.execute(
        """
        CREATE TRIGGER trg_mov_lote_bloqueia_update
        BEFORE UPDATE ON estoque_movimentacaolote
        FOR EACH ROW
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Movimentacao por lote e imutavel: use estorno.'
        """
    )
    schema_editor.execute(
        """
        CREATE TRIGGER trg_mov_lote_bloqueia_delete
        BEFORE DELETE ON estoque_movimentacaolote
        FOR EACH ROW
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Movimentacao por lote nao pode ser excluida: use estorno.'
        """
    )


def remover_triggers_movimentacao_lote(apps, schema_editor):
    if schema_editor.connection.vendor != 'mysql':
        return

    schema_editor.execute('DROP TRIGGER IF EXISTS trg_mov_lote_bloqueia_update')
    schema_editor.execute('DROP TRIGGER IF EXISTS trg_mov_lote_bloqueia_delete')


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ('estoque', '0004_rotulos_tipos_movimentacao'),
    ]

    operations = [
        migrations.CreateModel(
            name='LoteEstoque',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero_lote', models.CharField(max_length=100)),
                ('data_validade', models.DateField(blank=True, null=True)),
                ('saldo_atual', models.DecimalField(decimal_places=3, default=0, max_digits=12)),
                ('legado', models.BooleanField(default=False)),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('data_atualizacao', models.DateTimeField(auto_now=True)),
                (
                    'estoque',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='lotes',
                        to='estoque.estoque',
                    ),
                ),
            ],
            options={
                'ordering': ['estoque_id', 'data_validade', 'numero_lote', 'id'],
            },
        ),
        migrations.CreateModel(
            name='MovimentacaoLote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantidade', models.DecimalField(decimal_places=3, max_digits=12)),
                ('saldo_lote_resultante', models.DecimalField(decimal_places=3, max_digits=12)),
                (
                    'lote',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='movimentacoes',
                        to='estoque.loteestoque',
                    ),
                ),
                (
                    'movimentacao',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='alocacoes_lote',
                        to='estoque.movimentacaoestoque',
                    ),
                ),
            ],
            options={
                'ordering': ['movimentacao_id', 'id'],
            },
        ),
        migrations.AddConstraint(
            model_name='loteestoque',
            constraint=models.UniqueConstraint(
                fields=('estoque', 'numero_lote'),
                name='lote_unico_por_estoque',
            ),
        ),
        migrations.AddConstraint(
            model_name='loteestoque',
            constraint=models.CheckConstraint(
                condition=models.Q(('saldo_atual__gte', 0)),
                name='lote_saldo_nao_negativo',
            ),
        ),
        migrations.AddConstraint(
            model_name='loteestoque',
            constraint=models.CheckConstraint(
                condition=~models.Q(('numero_lote', '')),
                name='lote_numero_nao_vazio',
            ),
        ),
        migrations.AddConstraint(
            model_name='loteestoque',
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(('data_validade__isnull', True), ('legado', True))
                    | models.Q(('data_validade__isnull', False), ('legado', False))
                ),
                name='lote_validade_coerente',
            ),
        ),
        migrations.AddIndex(
            model_name='loteestoque',
            index=models.Index(fields=['estoque', 'data_validade'], name='lote_estoque_val_idx'),
        ),
        migrations.AddIndex(
            model_name='loteestoque',
            index=models.Index(fields=['data_validade', 'saldo_atual'], name='lote_validade_saldo_idx'),
        ),
        migrations.AddConstraint(
            model_name='movimentacaolote',
            constraint=models.CheckConstraint(
                condition=models.Q(('quantidade__gt', 0)),
                name='mov_lote_quantidade_positiva',
            ),
        ),
        migrations.AddConstraint(
            model_name='movimentacaolote',
            constraint=models.CheckConstraint(
                condition=models.Q(('saldo_lote_resultante__gte', 0)),
                name='mov_lote_saldo_nao_negativo',
            ),
        ),
        migrations.AddConstraint(
            model_name='movimentacaolote',
            constraint=models.UniqueConstraint(
                fields=('movimentacao', 'lote'),
                name='mov_lote_unico',
            ),
        ),
        migrations.RunPython(migrar_estoque_legado, reverter_estoque_legado),
        migrations.RunPython(criar_triggers_movimentacao_lote, remover_triggers_movimentacao_lote),
    ]
