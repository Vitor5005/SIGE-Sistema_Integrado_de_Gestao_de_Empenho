from decimal import Decimal

from django.db.models.signals import post_save
from django.dispatch import receiver

from cadastro.models import ItemGenerico
from estoque.models import Estoque, LoteEstoque


@receiver(post_save, sender=ItemGenerico)
def criar_estoque_do_genero(sender, instance, created, **kwargs):
    if created:
        estoque, _ = Estoque.objects.get_or_create(item_generico=instance)
        LoteEstoque.objects.get_or_create(
            estoque=estoque,
            numero_lote=LoteEstoque.NUMERO_LOTE_LEGADO,
            defaults={
                'data_validade': None,
                'saldo_atual': Decimal('0.000'),
                'legado': True,
            },
        )
