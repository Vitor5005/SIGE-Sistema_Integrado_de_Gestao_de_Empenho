from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from usuario.models import Usuario

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Informacoes adicionais', {'fields': ('papel',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informacoes adicionais', {'fields': ('papel',)}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'papel', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')