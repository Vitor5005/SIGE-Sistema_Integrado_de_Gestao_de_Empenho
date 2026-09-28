from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('estoque', '0003_alter_movimentacaoestoque_item_ordem'),
    ]

    operations = [
        migrations.AlterField(
            model_name='movimentacaoestoque',
            name='tipo',
            field=models.CharField(choices=[('ENTRADA_FORNECEDOR', 'Entrada de fornecedor'), ('CARGA_INICIAL', 'Carga inicial'), ('AJUSTE_POSITIVO', 'Inventário (sobra)'), ('AJUSTE_NEGATIVO', 'Inventário (falta)'), ('SAIDA_PRODUCAO', 'Consumo no preparo de refeições'), ('SAIDA_DOACAO', 'Doação'), ('SAIDA_PERDA', 'Perda ou vencimento'), ('ESTORNO', 'Estorno')], max_length=20),
        ),
    ]
