from django.contrib import admin

from cardapio.models import Cardapio, ItemCardapio


class ItemCardapioInline(admin.TabularInline):
    model = ItemCardapio
    extra = 0
    readonly_fields = ('quantidade_liberada', 'quantidade_consumida')


@admin.register(Cardapio)
class CardapioAdmin(admin.ModelAdmin):
    list_display = ('data', 'refeicao', 'estimativa_pessoas', 'status', 'criado_por')
    list_filter = ('status', 'refeicao')
    inlines = [ItemCardapioInline]
