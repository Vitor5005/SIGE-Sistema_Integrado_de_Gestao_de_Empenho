from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
#from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone
from utils.rbac import Papel
# Create your models here.

class Usuario(AbstractUser):
    PAPEL_CHOICES = Papel.CHOICES
    papel = models.CharField(
        max_length=5,
        choices=PAPEL_CHOICES,
        default=Papel.TECNICO_ADMINISTRATIVO
    )
    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
    def __str__(self):
        return f"{self.username} - {self.get_papel_display()}"


class HistoricoAuditoriaQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValidationError('Registros de auditoria são imutáveis.')

    def delete(self):
        raise ValidationError('Registros de auditoria não podem ser excluídos.')


class HistoricoAuditoria(models.Model):
    objects = HistoricoAuditoriaQuerySet.as_manager()

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='eventos_auditoria',
    )
    papel = models.CharField(max_length=5, blank=True)
    acao = models.CharField(max_length=40)
    recurso = models.CharField(max_length=50)
    entidade = models.CharField(max_length=100, blank=True)
    entidade_id = models.CharField(max_length=100, null=True, blank=True)
    valores_anteriores = models.JSONField(default=dict, blank=True)
    valores_novos = models.JSONField(default=dict, blank=True)
    permitido = models.BooleanField(default=True)
    detalhe = models.TextField(blank=True)
    data_hora = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-data_hora', '-id']
        verbose_name = 'Histórico de auditoria'
        verbose_name_plural = 'Históricos de auditoria'

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError('Registros de auditoria são imutáveis.')
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError('Registros de auditoria não podem ser excluídos.')

    def __str__(self):
        resultado = 'permitido' if self.permitido else 'negado'
        return f'{self.papel or "ANÔNIMO"} - {self.recurso}.{self.acao} ({resultado})'

class CodigoRedefiniçãoSenha(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    codigo = models.CharField(max_length=6)
    criado_em = models.DateTimeField(auto_now_add=True)
    expira_em = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.id:
            self.expira_em = timezone.now() + timezone.timedelta(minutes=10)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Código de redefinição para {self.usuario.username}"
