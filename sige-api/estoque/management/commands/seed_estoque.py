from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from cadastro.models import ItemGenerico
from utils.estoque_services import registrar_carga_inicial
from usuario.models import Usuario
from utils.rbac import Papel


ITENS = (
    ('ES0001', 'Ervas finas', 'un', 'tempS', '10', 'g', '246'),
    ('ES0002', 'Folha de louro', 'un', 'tempS', '10', 'g', '352'),
    ('ES0003', 'Linhaça', 'un', 'tempS', '200', 'g', '38'),
    ('ES0004', 'Linhaça', 'un', 'tempS', '500', 'g', '5'),
    ('ES0005', 'Arroz', 'KG', 'SM', None, None, '1430'),
    ('ES0006', 'Feijão carioca', 'KG', 'SM', None, None, '970'),
    ('ES0007', 'Açúcar', 'KG', 'SM', None, None, '258'),
    ('ES0008', 'Sal', 'KG', 'SM', None, None, '80'),
    ('ES0009', 'Leite integral', 'L', 'Lac', None, None, '1284'),
    ('ES0010', 'Creme de leite', 'un', 'Lac', '200', 'g', '210'),
    ('ES0011', 'Óleo de soja', 'un', 'Oli', '900', 'ml', '162'),
    ('ES0012', 'Azeite de dendê', 'un', 'Oli', '900', 'ml', '23'),
    ('ES0013', 'Azeite de dendê', 'un', 'Oli', '500', 'ml', '12'),
    ('ES0014', 'Mostarda', 'un', 'MolCo', '200', 'g', '91'),
    ('ES0015', 'Ketchup', 'un', 'MolCo', '390', 'g', '170'),
)

# TODO: incluir itens de "Bebidas e Complementos" e "Outros itens" somente
# após a definição dos códigos de categoria correspondentes.


class Command(BaseCommand):
    help = 'Cria dados de desenvolvimento para a carga inicial do estoque do R.U.'

    def handle(self, *args, **options):
        usuario, criado = Usuario.objects.get_or_create(
            username='estoquista',
            defaults={
                'first_name': 'Estoquista',
                'last_name': 'do R.U.',
                'email': 'estoquista@example.com',
                'papel': Papel.ESTOQUISTA,
                'is_active': True,
            },
        )
        usuario.papel = Papel.ESTOQUISTA
        usuario.is_active = True
        if criado:
            usuario.set_password('password123')
        usuario.save()

        for catmat, descricao, unidade, categoria, conteudo, unidade_embalagem, quantidade in ITENS:
            genero, _ = ItemGenerico.objects.get_or_create(
                catmat=catmat,
                defaults={
                    'descricao': descricao,
                    'unidade_medida': unidade,
                    'categoria': categoria,
                    'conteudo_embalagem': Decimal(conteudo) if conteudo else None,
                    'unidade_embalagem': unidade_embalagem,
                },
            )
            try:
                registrar_carga_inicial(
                    item_generico_id=genero.id,
                    quantidade=Decimal(quantidade),
                    justificativa='Carga inicial de desenvolvimento do estoque físico do R.U.',
                    usuario=usuario,
                    data_hora=timezone.now(),
                )
                self.stdout.write(self.style.SUCCESS(f'Carga inicial criada: {genero}'))
            except Exception as erro:
                if 'já possui carga inicial' in str(erro):
                    self.stdout.write(f'Carga inicial já existente: {genero}')
                    continue
                raise

        self.stdout.write(self.style.SUCCESS('Seed de estoque concluído.'))

