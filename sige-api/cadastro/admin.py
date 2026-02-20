from django.contrib import admin
from cadastro.models import Endereco, Fornecedor, ItemGenerico

class EnderecoAdmin(admin.ModelAdmin):
    list_display = ("id", "lagradouro", "numero", "bairro", "cep", "municipio", "estado")
    list_display_links = ("id", "lagradouro")
    search_fields = ("id",)
    
admin.site.register(Endereco, EnderecoAdmin)
    
class FornecedorAdmin(admin.ModelAdmin):
    list_display = ("id", "razao_social", "nome_fantasia", "cnpj", "telefone", "email", "endereco")
    list_display_links = ("id", "razao_social", "cnpj")
    search_fields = ("id", "razao_social", "cnpj")

admin.site.register(Fornecedor, FornecedorAdmin)

class ItemGenericoAdmin(admin.ModelAdmin):
    list_display = ("id", "catmat", "descricao", "unidade_medida", "categoria")
    list_display_links = ("id", "catmat", "descricao")
    search_fields = ("id", "catmat", "descricao")
    
admin.site.register(ItemGenerico, ItemGenericoAdmin)


# Register your models here.
