from django.contrib import admin
from entrega.models import OrdemEntrega, ItemOrdem

class OrdemEntregaAdmin(admin.ModelAdmin):
    list_display = ("id", "codigo", "empenho", "status", "data_emissao", "data_entrega", "valor_total_executado")
    list_display_links = ("id", "codigo")
    search_fields = ("id", "codigo")
    
admin.site.register(OrdemEntrega, OrdemEntregaAdmin)

class ItemOrdemAdmin(admin.ModelAdmin):
    list_display = ("id", "ordem_entrega", "item_empenho", "quantidade_solicitada", "quantidade_entregue", "observacao")
    list_display_links = ("id",)
    search_fields = ("id",)

admin.site.register(ItemOrdem, ItemOrdemAdmin)

# Register your models here.
