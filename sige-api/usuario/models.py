from django.db import models
from django.contrib.auth.models import AbstractUser
#from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone
# Create your models here.

class Usuario(AbstractUser):
    PAPEL_CHOICES =[
        ('ADMIN', 'Administrador'),
        ('TECNI','Tecnico'),
    ]
    papel = models.CharField(
        max_length=5,
        choices=PAPEL_CHOICES,
        default='TECNI'
    )
    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
    def __str__(self):
        return f"{self.username} - {self.get_papel_display()}"

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