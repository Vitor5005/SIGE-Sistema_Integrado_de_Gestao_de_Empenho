from django.db.models.signals import post_save
from django.dispatch import receiver

from cadastro.models import ItemGenerico
from estoque.models import Estoque


@receiver(post_save, sender=ItemGenerico)
def criar_estoque_do_genero(sender, instance, created, **kwargs):
    if created:
        Estoque.objects.get_or_create(item_generico=instance)
