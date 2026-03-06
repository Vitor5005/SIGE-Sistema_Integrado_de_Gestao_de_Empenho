from django.db import models
from django.contrib.auth.models import AbstractUser


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

