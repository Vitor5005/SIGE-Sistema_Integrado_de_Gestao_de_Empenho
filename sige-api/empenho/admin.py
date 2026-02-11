from django.contrib import admin
from empenho.models import Empenho, ItemEmpenho, OperacaoItem

class EmpenhoAdmin(admin.ModelAdmin):
    list_display = ("id", "codigo", "ata", "valor_total", "saldo_utilizado")
    list_display_links = ("id", "codigo")
    search_fields = ("id", "codigo")

admin.site.register(Empenho, EmpenhoAdmin)

class ItemEmpenhoAdmin(admin.ModelAdmin):
    list_display = ("id", "empenho", "item_ata", "quantidade_atual")
    list_display_links = ("id", )
    search_fields = ("id", )
    
admin.site.register(ItemEmpenho, ItemEmpenhoAdmin)
    
class OperacaoItemAdmin(admin.ModelAdmin):
    list_display = ("id", "item_empenho", "tipo", "valor", "data")
    list_display_links = ("id",)
    search_fields = ("id",)

admin.site.register(OperacaoItem, OperacaoItemAdmin)

# Register your models here.
