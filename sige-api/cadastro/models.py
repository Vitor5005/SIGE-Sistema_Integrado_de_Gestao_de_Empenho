from django.db import models

# Create your models here.
class Endereco(models.Model):
    ESTADOS = (
        ('AC', 'Acre'), ('AL', 'Alagoas'), ('AP', 'Amapá'), ('AM', 'Amazonas'),
        ('BA', 'Bahia'), ('CE', 'Ceará'), ('DF', 'Distrito Federal'), ('ES', 'Espírito Santo'),
        ('GO', 'Goiás'), ('MA', 'Maranhão'), ('MT', 'Mato Grosso'), ('MS', 'Mato Grosso do Sul'),
        ('MG', 'Minas Gerais'), ('PA', 'Pará'), ('PB', 'Paraíba'), ('PR', 'Paraná'),
        ('PE', 'Pernambuco'), ('PI', 'Piauí'), ('RJ', 'Rio de Janeiro'), ('RN', 'Rio Grande do Norte'),
        ('RS', 'Rio Grande do Sul'), ('RO', 'Rondônia'), ('RR', 'Roraima'), ('SC', 'Santa Catarina'),
        ('SP', 'São Paulo'), ('SE', 'Sergipe'), ('TO', 'Tocantins'),
    )

    lagradouro = models.CharField(max_length=255)
    numero = models.CharField(max_length=20)
    bairro = models.CharField(max_length=100)
    cep = models.CharField(max_length=8)
    municipio = models.CharField(max_length=100)
    estado = models.CharField(max_length=2, choices=ESTADOS)
    
    def __str__(self):
        return f"{self.lagradouro}, {self.numero} - {self.municipio}/{self.estado}"
    
class Fornecedor(models.Model):
    razao_social = models.CharField(max_length=255)
    nome_fantasia = models.CharField(max_length=255)
    cnpj = models.CharField(max_length=18,unique=True, blank=False, null=False, verbose_name="CNPJ")
    telefone = models.CharField(max_length=20,blank=True,null=True)
    email = models.EmailField(max_length=255,blank=True,null=True)
    endereco = models.ForeignKey(Endereco, on_delete=models.PROTECT,related_name='fornecedores')
    
    def __str__(self):
        return f"{self.nome_fantasia} - {self.cnpj}"

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
        ("lata", "Lata"),
        ("un", "Unidade (UN)"),
    )
    unidade_medida = models.CharField(max_length=5, choices=unidades_de_medida, default="KG", blank=False, null=False)
    
    categorias_de_alimento = (
        ("tempS", "Tempero Secos"),
        ("SM", "Secos / Mercearia"),
        ("Lac", "Lácteos e Derivados"),
        ("Oli", "Óleos, Azeites e Vinagres"), 
        ("MolCo", "Molhos e Condimentos"),
        ("Fr","Frutas"), 
        ("Le","Legumes"),
        ("Pr","Proteínas")
    )
    categoria = models.CharField(max_length=5, choices=categorias_de_alimento, blank=False, null=False)
    conteudo_embalagem = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
    )
    unidades_embalagem = (
        ('g', 'Grama'),
        ('kg', 'Quilograma'),
        ('ml', 'Mililitro'),
        ('L', 'Litro'),
    )
    unidade_embalagem = models.CharField(
        max_length=5,
        choices=unidades_embalagem,
        null=True,
        blank=True,
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(conteudo_embalagem__isnull=True, unidade_embalagem__isnull=True)
                    | models.Q(
                        conteudo_embalagem__gt=0,
                        unidade_embalagem__in=['g', 'kg', 'ml', 'L'],
                    )
                ),
                name='item_generico_embalagem_coerente',
            ),
        ]
    
    def __str__(self):
        return f"{self.catmat} - {self.descricao}"
