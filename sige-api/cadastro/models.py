from django.db import models

# Create your models here.
class Endereco(models.Model):
    lagradouro = models.CharField(max_length=255)
    numero = models.CharField(max_length=20)
    bairro = models.CharField(max_length=100)
    cep = models.CharField(max_length=8)
    municipio = models.CharField(max_length=100)
    estado = models.CharField(max_length=2)
    
    def __str__(self):
        return f"{self.lagradouro}, {self.numero} - {self.municipio}/{self.estado}"
class Fornecedor(models.Model):
    razao_social = models.CharField(max_length=255)
    nome_fantasia = models.CharField(max_length=255)
    cnpj = models.CharField(max_length=18,unique=True)
    telefone = models.CharField(max_length=20,blank=True,null=True)
    email = models.EmailField(max_length=255,blank=True,null=True)
    endereco = models.ForeignKey(Endereco, on_delete=models.PROTECT,related_name='fornecedores')




