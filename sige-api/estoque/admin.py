from django.contrib import admin

from estoque.models import (
    Estoque,
    Inventario,
    ItemInventario,
    LoteEstoque,
    MovimentacaoEstoque,
    MovimentacaoLote,
)


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


@admin.register(LoteEstoque)
class LoteEstoqueAdmin(admin.ModelAdmin):
    list_display = (
        'estoque',
        'numero_lote',
        'data_validade',
        'saldo_atual',
        'legado',
        'data_atualizacao',
    )
    search_fields = (
        'estoque__item_generico__catmat',
        'estoque__item_generico__descricao',
        'numero_lote',
    )
    list_filter = ('legado', 'data_validade')
    readonly_fields = [field.name for field in LoteEstoque._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(MovimentacaoLote)
class MovimentacaoLoteAdmin(admin.ModelAdmin):
    list_display = ('movimentacao', 'lote', 'quantidade', 'saldo_lote_resultante')
    readonly_fields = [field.name for field in MovimentacaoLote._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(Inventario)
admin.site.register(ItemInventario)
