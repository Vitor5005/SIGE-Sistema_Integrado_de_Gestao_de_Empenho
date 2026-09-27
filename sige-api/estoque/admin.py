from django.contrib import admin

from estoque.models import Estoque, Inventario, ItemInventario, MovimentacaoEstoque


@admin.register(Estoque)
class EstoqueAdmin(admin.ModelAdmin):
    list_display = ('item_generico', 'saldo_atual', 'data_atualizacao')
    readonly_fields = ('item_generico', 'saldo_atual', 'data_atualizacao')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(MovimentacaoEstoque)
class MovimentacaoEstoqueAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'estoque', 'quantidade', 'sentido', 'data_hora', 'usuario')
    readonly_fields = [field.name for field in MovimentacaoEstoque._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(Inventario)
admin.site.register(ItemInventario)
