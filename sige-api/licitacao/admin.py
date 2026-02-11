from django.contrib import admin
from licitacao.models import Licitacao, Ata, ItemAta

class LicitacaoAdmin(admin.ModelAdmin):
    list_display = ("id", "numero_licitacao", "validade", "data_abertura")
    list_display_links =  ("id", "numero_licitacao")
    search_fields = ("id", "numero_licitacao")
    
admin.site.register(Licitacao, LicitacaoAdmin)

class AtaAdmin(admin.ModelAdmin):
    list_display = ("id", "numero_ata", "ata_saldo_total", "licitacao", "fornecedor")
    list_display_links = ("id", "numero_ata")
    search_fields = ("id", "numero_ata")
    
admin.site.register(Ata, AtaAdmin)

class ItemAtaAdmin(admin.ModelAdmin):
    list_display = ("id", "ata", "item_generico", "marca", "quantidade_licitada", "valor_unitario")
    list_display_links = ("id", "marca")
    search_fields = ("id", "marca")
    
admin.site.register(ItemAta, ItemAtaAdmin)
