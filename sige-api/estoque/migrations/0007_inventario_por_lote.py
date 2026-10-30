import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('estoque', '0006_merge_lotes_cardapio'),
    ]

    operations = [
        migrations.AlterField(
            model_name='movimentacaoestoque',
            name='item_inventario',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='movimentacoes_estoque',
                to='estoque.iteminventario',
            ),
        ),
        migrations.CreateModel(
            name='ContagemLoteInventario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('saldo_sistema', models.DecimalField(decimal_places=3, max_digits=12)),
                ('quantidade_contada', models.DecimalField(decimal_places=3, max_digits=12)),
                (
                    'item_inventario',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='contagens_lote',
                        to='estoque.iteminventario',
                    ),
                ),
                (
                    'lote',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='contagens_inventario',
                        to='estoque.loteestoque',
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name='contagemloteinventario',
            constraint=models.UniqueConstraint(
                fields=('item_inventario', 'lote'),
                name='contagem_lote_unica_por_item',
            ),
        ),
        migrations.AddConstraint(
            model_name='contagemloteinventario',
            constraint=models.CheckConstraint(
                condition=models.Q(('saldo_sistema__gte', 0), ('quantidade_contada__gte', 0)),
                name='contagem_lote_quantidades_nao_negativas',
            ),
        ),
    ]
