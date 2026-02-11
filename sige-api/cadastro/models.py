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
    cnpj = models.CharField(max_length=18,unique=True, blank=False, null=False, verbose_name="CNPJ")
    telefone = models.CharField(max_length=20,blank=True,null=True)
    email = models.EmailField(max_length=255,blank=True,null=True)
    endereco = models.ForeignKey(Endereco, on_delete=models.PROTECT,related_name='fornecedores')

class ItemGenerico(models.Model):
    catmat = models.CharField(max_length = 6, unique=True, blank=False, null=False)
    descricao = models.CharField(max_length=300)
    unidades_de_medida = (
        ("KG", "Quilograma (KG)"),
        ("G", "Grama (G)"),
        ("L", "Litro (L)"),
        ("mL", "Mililitro (mL)"),
        ("duzia", "Duzia"),
        ("cento", "Cento"),
        ("PCT", "Pacote (PCT)"),
        ("CX", "Caixa (CX)"),
        ("FND", "Fardo (FND)"),
        ("GAR", "Garrafa (GAR)"),
        ("lata", "Lata")
    )
    unidade_medida = models.CharField(max_length=5, choices=unidades_de_medida, default="KG", blank=False, null=False)
    
    categorias_de_alimento = (
        ("tempS", "Tempero Secos"),
        ("SM", "Secos / Mercearia"),
        ("Lac", "Lácteos e Derivados"),
        ("Oli", "Óleos, Azeites e Vinagres"), 
        ("MolCo", "Molhos e Condimentos"),
        ("Fr","Frutas"), 
        ("Le","Legumes")
    )
    categoria = models.CharField(max_length=5, choices=categorias_de_alimento, blank=False, null=False)
    