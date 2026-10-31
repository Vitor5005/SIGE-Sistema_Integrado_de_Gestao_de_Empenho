"""
Cria um usuário para cada papel do sistema: Diretor, Técnico Administrativo,
Nutricionista e Estoquista.

Usuários: diretor, tecnico, nutricionista e estoquista.
Também popula a demonstração (fornecedores, licitações, atas, empenhos, entregas,
recebimentos) e a carga inicial do estoque físico do R.U.

Uso:  python seed.py                               # senha 'senha123' para os quatro
      SEED_SENHA='minha-senha' python seed.py   # outra senha para os quatro (use em produção)
"""
import os
import random
import sys
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sige_api.settings')

import django

django.setup()

from django.db import transaction
from django.db.models import Count, Sum
from django.utils import timezone

from cadastro.models import Endereco, Fornecedor, ItemGenerico
from licitacao.models import Licitacao, Ata, ItemAta
from empenho.models import Empenho, ItemEmpenho, OperacaoItem
from empenho.services import registrar_operacao_item
from entrega.models import OrdemEntrega, ItemOrdem, PendenciaFornecedor
from estoque.models import (
    Estoque,
    Inventario,
    ItemInventario,
    LoteEstoque,
    MovimentacaoEstoque,
    MovimentacaoLote,
)
from usuario.models import Usuario
from utils.estoque_services import FUSO_ESTOQUE, registrar_carga_inicial, registrar_recebimento
from utils.rbac import Papel


SEED_RANDOM = 20260927
ANO_REFERENCIA = timezone.localdate().year
MAX_VALOR_MONETARIO = Decimal('1000000.00')
QTD_LICITADA_MIN = 20
QTD_LICITADA_MAX = 120
PCT_EMPENHO_MIN = 5
PCT_EMPENHO_MAX = 30
TIPOS_LICITACAO = ['PE', 'TP', 'CC', 'DL', 'IN']
UNIDADES_DECIMAIS = {'KG', 'L', 'G', 'mL'}


NOMES_FORNECEDORES = [
    {'razao': 'ALIMENTOS NATURAIS LTDA', 'fantasia': 'Alimentos Naturais'},
    {'razao': 'DISTRIBUIDORA DE ALIMENTOS JB', 'fantasia': 'Dist. JB'},
    {'razao': 'FORNECEDORA DE CARNES PREMIUM', 'fantasia': 'Carnes Premium'},
    {'razao': 'FRUTAS E VERDURAS DO ACRE', 'fantasia': 'Frutas & Verduras'},
    {'razao': 'LATICÍNIOS DO BRASIL LTDA', 'fantasia': 'Laticínios Brasil'},
    {'razao': 'PRODUTOS SECOS E MERCEARIA', 'fantasia': 'Mercearia Central'},
    {'razao': 'DISTRIBUIDORA DE CONGELADOS', 'fantasia': 'Congelados Ltda'},
    {'razao': 'FORNECEDORA DE BEBIDAS SA', 'fantasia': 'Bebidas Select'},
]

ENDERECOS = [
    {'logradouro': 'Rua do Comércio', 'numero': '123', 'bairro': 'Centro', 'municipio': 'Rio Branco', 'estado': 'AC', 'cep': '69900000'},
    {'logradouro': 'Avenida Getúlio Vargas', 'numero': '456', 'bairro': 'Bosque', 'municipio': 'Rio Branco', 'estado': 'AC', 'cep': '69900100'},
    {'logradouro': 'Rua 6 de Agosto', 'numero': '789', 'bairro': 'Centro', 'municipio': 'Rio Branco', 'estado': 'AC', 'cep': '69900200'},
    {'logradouro': 'Avenida Brasil', 'numero': '321', 'bairro': 'Distrito Industrial', 'municipio': 'Rio Branco', 'estado': 'AC', 'cep': '69920000'},
    {'logradouro': 'Rua Rui Barbosa', 'numero': '654', 'bairro': 'Taquari', 'municipio': 'Rio Branco', 'estado': 'AC', 'cep': '69903000'},
]

ITENS_ALIMENTOS = [
    {'catmat': '100001', 'descricao': 'Arroz Integral', 'categoria': 'SM', 'unidade': 'KG', 'conteudo_embalagem': Decimal('5.00'), 'unidade_embalagem': 'kg'},
    {'catmat': '100002', 'descricao': 'Feijão Carioca', 'categoria': 'SM', 'unidade': 'KG', 'conteudo_embalagem': Decimal('1.00'), 'unidade_embalagem': 'kg'},
    {'catmat': '100003', 'descricao': 'Macarrão Integral', 'categoria': 'SM', 'unidade': 'G', 'conteudo_embalagem': Decimal('500.00'), 'unidade_embalagem': 'g'},
    {'catmat': '100004', 'descricao': 'Açúcar Cristal', 'categoria': 'SM', 'unidade': 'KG', 'conteudo_embalagem': Decimal('1.00'), 'unidade_embalagem': 'kg'},
    {'catmat': '100005', 'descricao': 'Sal Refinado', 'categoria': 'SM', 'unidade': 'KG', 'conteudo_embalagem': Decimal('1.00'), 'unidade_embalagem': 'kg'},
    {'catmat': '200001', 'descricao': 'Leite Integral', 'categoria': 'Lac', 'unidade': 'L', 'conteudo_embalagem': Decimal('1.00'), 'unidade_embalagem': 'L'},
    {'catmat': '200002', 'descricao': 'Queijo Meia Cura', 'categoria': 'Lac', 'unidade': 'G', 'conteudo_embalagem': Decimal('500.00'), 'unidade_embalagem': 'g'},
    {'catmat': '200003', 'descricao': 'Iogurte Natural', 'categoria': 'Lac', 'unidade': 'mL', 'conteudo_embalagem': Decimal('170.00'), 'unidade_embalagem': 'ml'},
    {'catmat': '200004', 'descricao': 'Manteiga', 'categoria': 'Lac', 'unidade': 'G', 'conteudo_embalagem': Decimal('200.00'), 'unidade_embalagem': 'g'},
    {'catmat': '300001', 'descricao': 'Óleo de Soja', 'categoria': 'Oli', 'unidade': 'mL', 'conteudo_embalagem': Decimal('900.00'), 'unidade_embalagem': 'ml'},
    {'catmat': '300002', 'descricao': 'Azeite Extra Virgem', 'categoria': 'Oli', 'unidade': 'mL', 'conteudo_embalagem': Decimal('500.00'), 'unidade_embalagem': 'ml'},
    {'catmat': '300003', 'descricao': 'Vinagre Branco', 'categoria': 'Oli', 'unidade': 'mL', 'conteudo_embalagem': Decimal('750.00'), 'unidade_embalagem': 'ml'},
    {'catmat': '400001', 'descricao': 'Banana Prata', 'categoria': 'Fr', 'unidade': 'KG', 'conteudo_embalagem': None, 'unidade_embalagem': None},
    {'catmat': '400002', 'descricao': 'Maçã Gala', 'categoria': 'Fr', 'unidade': 'KG', 'conteudo_embalagem': None, 'unidade_embalagem': None},
    {'catmat': '400003', 'descricao': 'Laranja Pera', 'categoria': 'Fr', 'unidade': 'KG', 'conteudo_embalagem': None, 'unidade_embalagem': None},
    {'catmat': '500001', 'descricao': 'Alface Crespa', 'categoria': 'Le', 'unidade': 'KG', 'conteudo_embalagem': None, 'unidade_embalagem': None},
    {'catmat': '500002', 'descricao': 'Tomate', 'categoria': 'Le', 'unidade': 'KG', 'conteudo_embalagem': None, 'unidade_embalagem': None},
    {'catmat': '500003', 'descricao': 'Cebola', 'categoria': 'Le', 'unidade': 'KG', 'conteudo_embalagem': None, 'unidade_embalagem': None},
    {'catmat': '500004', 'descricao': 'Batata Doce', 'categoria': 'Le', 'unidade': 'KG', 'conteudo_embalagem': None, 'unidade_embalagem': None},
    {'catmat': '600001', 'descricao': 'Frango Congelado', 'categoria': 'Pr', 'unidade': 'KG', 'conteudo_embalagem': None, 'unidade_embalagem': None},
    {'catmat': '600002', 'descricao': 'Carne Bovina', 'categoria': 'Pr', 'unidade': 'KG', 'conteudo_embalagem': None, 'unidade_embalagem': None},
    {'catmat': '600003', 'descricao': 'Ovos Caipira', 'categoria': 'Pr', 'unidade': 'duzia', 'conteudo_embalagem': None, 'unidade_embalagem': None},
]

# Gêneros que só existem no estoque físico do R.U. (não entram em atas/empenhos):
# recebem uma carga inicial de estoque registrada pelo estoquista.
ITENS_CARGA_INICIAL = [
    {'catmat': 'ES0001', 'descricao': 'Ervas finas', 'categoria': 'tempS', 'unidade': 'un', 'conteudo_embalagem': Decimal('10'), 'unidade_embalagem': 'g', 'quantidade': Decimal('246')},
    {'catmat': 'ES0002', 'descricao': 'Folha de louro', 'categoria': 'tempS', 'unidade': 'un', 'conteudo_embalagem': Decimal('10'), 'unidade_embalagem': 'g', 'quantidade': Decimal('352')},
    {'catmat': 'ES0003', 'descricao': 'Linhaça', 'categoria': 'tempS', 'unidade': 'un', 'conteudo_embalagem': Decimal('200'), 'unidade_embalagem': 'g', 'quantidade': Decimal('38')},
    {'catmat': 'ES0004', 'descricao': 'Linhaça', 'categoria': 'tempS', 'unidade': 'un', 'conteudo_embalagem': Decimal('500'), 'unidade_embalagem': 'g', 'quantidade': Decimal('5')},
    {'catmat': 'ES0005', 'descricao': 'Arroz', 'categoria': 'SM', 'unidade': 'KG', 'conteudo_embalagem': None, 'unidade_embalagem': None, 'quantidade': Decimal('1430')},
    {'catmat': 'ES0006', 'descricao': 'Feijão carioca', 'categoria': 'SM', 'unidade': 'KG', 'conteudo_embalagem': None, 'unidade_embalagem': None, 'quantidade': Decimal('970')},
    {'catmat': 'ES0007', 'descricao': 'Açúcar', 'categoria': 'SM', 'unidade': 'KG', 'conteudo_embalagem': None, 'unidade_embalagem': None, 'quantidade': Decimal('258')},
    {'catmat': 'ES0008', 'descricao': 'Sal', 'categoria': 'SM', 'unidade': 'KG', 'conteudo_embalagem': None, 'unidade_embalagem': None, 'quantidade': Decimal('80')},
    {'catmat': 'ES0009', 'descricao': 'Leite integral', 'categoria': 'Lac', 'unidade': 'L', 'conteudo_embalagem': None, 'unidade_embalagem': None, 'quantidade': Decimal('1284')},
    {'catmat': 'ES0010', 'descricao': 'Creme de leite', 'categoria': 'Lac', 'unidade': 'un', 'conteudo_embalagem': Decimal('200'), 'unidade_embalagem': 'g', 'quantidade': Decimal('210')},
    {'catmat': 'ES0011', 'descricao': 'Óleo de soja', 'categoria': 'Oli', 'unidade': 'un', 'conteudo_embalagem': Decimal('900'), 'unidade_embalagem': 'ml', 'quantidade': Decimal('162')},
    {'catmat': 'ES0012', 'descricao': 'Azeite de dendê', 'categoria': 'Oli', 'unidade': 'un', 'conteudo_embalagem': Decimal('900'), 'unidade_embalagem': 'ml', 'quantidade': Decimal('23')},
    {'catmat': 'ES0013', 'descricao': 'Azeite de dendê', 'categoria': 'Oli', 'unidade': 'un', 'conteudo_embalagem': Decimal('500'), 'unidade_embalagem': 'ml', 'quantidade': Decimal('12')},
    {'catmat': 'ES0014', 'descricao': 'Mostarda', 'categoria': 'MolCo', 'unidade': 'un', 'conteudo_embalagem': Decimal('200'), 'unidade_embalagem': 'g', 'quantidade': Decimal('91')},
    {'catmat': 'ES0015', 'descricao': 'Ketchup', 'categoria': 'MolCo', 'unidade': 'un', 'conteudo_embalagem': Decimal('390'), 'unidade_embalagem': 'g', 'quantidade': Decimal('170')},
]
# TODO: incluir itens de "Bebidas e Complementos" e "Outros itens" somente
# após a definição dos códigos de categoria correspondentes.

FAIXAS_PRECO_UNITARIO = {
    '100001': (Decimal('5.50'), Decimal('9.50')),
    '100002': (Decimal('6.50'), Decimal('11.50')),
    '100003': (Decimal('0.02'), Decimal('0.08')),
    '100004': (Decimal('3.80'), Decimal('6.50')),
    '100005': (Decimal('1.80'), Decimal('4.20')),
    '200001': (Decimal('3.80'), Decimal('6.90')),
    '200002': (Decimal('0.05'), Decimal('0.16')),
    '200003': (Decimal('0.01'), Decimal('0.04')),
    '200004': (Decimal('0.03'), Decimal('0.12')),
    '300001': (Decimal('0.01'), Decimal('0.03')),
    '300002': (Decimal('0.02'), Decimal('0.08')),
    '300003': (Decimal('0.01'), Decimal('0.03')),
    '400001': (Decimal('3.20'), Decimal('7.50')),
    '400002': (Decimal('4.90'), Decimal('10.90')),
    '400003': (Decimal('2.80'), Decimal('6.90')),
    '500001': (Decimal('2.50'), Decimal('5.80')),
    '500002': (Decimal('4.00'), Decimal('8.90')),
    '500003': (Decimal('2.90'), Decimal('6.20')),
    '500004': (Decimal('2.20'), Decimal('5.10')),
    '600001': (Decimal('9.50'), Decimal('16.90')),
    '600002': (Decimal('24.90'), Decimal('44.90')),
    '600003': (Decimal('10.00'), Decimal('22.00')),
}


def validar_catalogo_seed():
    unidades_validas = {valor for valor, _ in ItemGenerico.unidades_de_medida}
    categorias_validas = {valor for valor, _ in ItemGenerico.categorias_de_alimento}
    embalagens_validas = {valor for valor, _ in ItemGenerico.unidades_embalagem}

    for item in ITENS_ALIMENTOS + ITENS_CARGA_INICIAL:
        catmat = item.get('catmat')
        descricao = item.get('descricao')
        unidade = item.get('unidade')
        categoria = item.get('categoria')
        conteudo_embalagem = item.get('conteudo_embalagem')
        unidade_embalagem = item.get('unidade_embalagem')

        if not catmat:
            raise RuntimeError('CATMAT ausente no catálogo da seed.')
        if not descricao:
            raise RuntimeError(f'CATMAT {catmat}: descrição ausente.')
        if unidade not in unidades_validas:
            raise RuntimeError(f'CATMAT {catmat}: unidade inválida: {unidade!r}.')
        if categoria not in categorias_validas:
            raise RuntimeError(f'CATMAT {catmat}: categoria inválida: {categoria!r}.')

        if conteudo_embalagem is None and unidade_embalagem is None:
            continue
        if conteudo_embalagem is None or unidade_embalagem is None:
            raise RuntimeError(
                f'CATMAT {catmat}: conteúdo e unidade de embalagem devem ser informados juntos.'
            )
        if conteudo_embalagem <= 0:
            raise RuntimeError(f'CATMAT {catmat}: conteúdo de embalagem inválido: {conteudo_embalagem!r}.')
        if unidade_embalagem not in embalagens_validas:
            raise RuntimeError(
                f'CATMAT {catmat}: unidade de embalagem inválida: {unidade_embalagem!r}.'
            )


def formatar_codigo_licitacao(tipo: str, numero: int, ano: int) -> str:
    return f'{tipo} {numero:03d}/{ano}'


def formatar_codigo_ata(numero: int, ano: int) -> str:
    return f'ARP {numero:03d}/{ano}'


def formatar_codigo_empenho(numero: int, ano: int) -> str:
    return f'{ano}NE{numero:06d}'


def limitar_valor_monetario(valor: Decimal) -> Decimal:
    return min(valor.quantize(Decimal('0.01')), MAX_VALOR_MONETARIO)


def arredondar_quantidade_por_unidade(valor: Decimal, unidade: str, permitir_zero: bool = True) -> Decimal:
    if unidade in UNIDADES_DECIMAIS:
        quantidade = valor.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        if not permitir_zero and quantidade == Decimal('0.00') and valor > Decimal('0'):
            return Decimal('0.01')
        return quantidade
    quantidade = valor.to_integral_value(rounding=ROUND_HALF_UP)
    if not permitir_zero and quantidade == Decimal('0') and valor > Decimal('0'):
        return Decimal('1')
    return quantidade


def gerar_quantidade_licitada_por_unidade(unidade: str) -> Decimal:
    if unidade in UNIDADES_DECIMAIS:
        return Decimal(random.randint(QTD_LICITADA_MIN * 100, QTD_LICITADA_MAX * 100)) / Decimal(100)
    return Decimal(random.randint(QTD_LICITADA_MIN, QTD_LICITADA_MAX))


def gerar_valor_unitario_item(catmat: str) -> Decimal:
    minimo, maximo = FAIXAS_PRECO_UNITARIO[catmat]
    minimo_centavos = int((minimo * 100).to_integral_value(rounding=ROUND_HALF_UP))
    maximo_centavos = int((maximo * 100).to_integral_value(rounding=ROUND_HALF_UP))
    return (Decimal(random.randint(minimo_centavos, maximo_centavos)) / Decimal(100)).quantize(
        Decimal('0.01'), rounding=ROUND_HALF_UP
    )


SENHA_PADRAO = os.environ.get('SEED_SENHA') or 'senha123'


def create_usuarios():
    """Garante um perfil ativo de cada papel, todos com a senha SENHA_PADRAO."""
    perfis = (
        ('diretor', Papel.DIRETOR, 'Diretor', 'SIGE', 'diretor@example.com'),
        ('tecnico', Papel.TECNICO_ADMINISTRATIVO, 'Técnico', 'Administrativo', 'tecnico@example.com'),
        ('nutricionista', Papel.NUTRICIONISTA, 'Nutricionista', 'SIGE', 'nutricionista@example.com'),
        ('estoquista', Papel.ESTOQUISTA, 'Estoquista', 'SIGE', 'estoquista@example.com'),
    )
    usuarios = {}
    for username, papel, first_name, last_name, email in perfis:
        usuario, _ = Usuario.objects.get_or_create(
            username=username,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'papel': papel,
                'is_staff': papel == Papel.DIRETOR,
                'is_superuser': papel == Papel.DIRETOR,
                'is_active': True,
            },
        )
        usuario.first_name = first_name
        usuario.last_name = last_name
        usuario.email = email
        usuario.papel = papel
        usuario.is_active = True
        if papel == Papel.DIRETOR:
            usuario.is_staff = True
            usuario.is_superuser = True
        usuario.set_password(SENHA_PADRAO)
        usuario.save()
        usuarios[papel] = usuario
    return usuarios


def seed_enderecos():
    return [
        Endereco.objects.create(
            lagradouro=dados['logradouro'],
            numero=dados['numero'],
            bairro=dados['bairro'],
            cep=''.join(caractere for caractere in dados['cep'] if caractere.isdigit())[:8],
            municipio=dados['municipio'],
            estado=dados['estado'],
        )
        for dados in ENDERECOS
    ]


def seed_fornecedores(enderecos):
    fornecedores = []
    for indice, dados in enumerate(NOMES_FORNECEDORES):
        fornecedores.append(
            Fornecedor.objects.create(
                razao_social=dados['razao'],
                nome_fantasia=dados['fantasia'],
                cnpj=(
                    f'{random.randint(10, 99)}.{random.randint(100, 999)}.'
                    f'{random.randint(100, 999)}/0001-{random.randint(10, 99)}'
                ),
                telefone=f'({random.randint(61, 99)}) {random.randint(98000, 99999)}-{random.randint(1000, 9999)}',
                email=f"contato{indice}@{dados['fantasia'].lower().replace(' ', '')}.com.br",
                endereco=enderecos[indice % len(enderecos)],
            )
        )
    return fornecedores


def seed_itens_genericos():
    itens = []
    for dados in ITENS_ALIMENTOS:
        itens.append(
            ItemGenerico.objects.create(
                catmat=dados['catmat'],
                descricao=dados['descricao'],
                unidade_medida=dados['unidade'],
                categoria=dados['categoria'],
                conteudo_embalagem=dados['conteudo_embalagem'],
                unidade_embalagem=dados['unidade_embalagem'],
            )
        )
    return itens


def seed_licitacoes(n=3):
    hoje = timezone.localdate()
    licitacoes = []
    for indice in range(n):
        data_abertura = hoje - timedelta(days=random.randint(30, 180))
        licitacoes.append(
            Licitacao.objects.create(
                numero_licitacao=formatar_codigo_licitacao(
                    tipo=random.choice(TIPOS_LICITACAO),
                    numero=indice + 1,
                    ano=data_abertura.year,
                ),
                validade=random.randint(12, 24),
                data_abertura=data_abertura,
                descricao=f'Licitação válida para aquisição de produtos alimentícios — lote {indice + 1}',
                atual=False,
            )
        )
    return licitacoes


def seed_licitacoes_expiradas(n=3):
    hoje = timezone.localdate()
    licitacoes = []
    for indice in range(n):
        data_abertura = hoje - timedelta(days=random.randint(540, 900))
        licitacoes.append(
            Licitacao.objects.create(
                numero_licitacao=formatar_codigo_licitacao(
                    tipo=random.choice(TIPOS_LICITACAO),
                    numero=n + indice + 1,
                    ano=data_abertura.year,
                ),
                validade=random.randint(3, 8),
                data_abertura=data_abertura,
                descricao=f'Licitação expirada para aquisição de produtos alimentícios — lote {indice + 1}',
                atual=False,
            )
        )
    return licitacoes


def seed_atas(licitacoes, fornecedores):
    atas = []
    contador = 1
    for licitacao in licitacoes:
        for fornecedor in random.sample(fornecedores, k=min(2, len(fornecedores))):
            atas.append(
                Ata.objects.create(
                    numero_ata=formatar_codigo_ata(contador, licitacao.data_abertura.year),
                    ata_saldo_total=Decimal('0.00'),
                    licitacao=licitacao,
                    fornecedor=fornecedor,
                )
            )
            contador += 1
    return atas


def _itens_obrigatorios_para_ata(indice_ata, itens_genericos):
    grupos = {
        0: itens_genericos[0:8],
        1: itens_genericos[8:16],
        3: itens_genericos[16:],
    }
    return grupos.get(indice_ata, [])


def seed_itens_ata(atas, itens_genericos):
    marcas = ['Premium', 'Padrão', 'Integral', 'Orgânico']
    itens_ata = []
    for indice_ata, ata in enumerate(atas):
        obrigatorios = _itens_obrigatorios_para_ata(indice_ata, itens_genericos)
        quantidade = max(len(obrigatorios), random.randint(3, 8))
        extras_disponiveis = [item for item in itens_genericos if item not in obrigatorios]
        selecionados = obrigatorios + random.sample(
            extras_disponiveis,
            k=min(quantidade - len(obrigatorios), len(extras_disponiveis)),
        )
        total_ata = Decimal('0.00')
        for item_generico in selecionados:
            quantidade_licitada = gerar_quantidade_licitada_por_unidade(item_generico.unidade_medida)
            valor_unitario = gerar_valor_unitario_item(item_generico.catmat)
            item_ata = ItemAta.objects.create(
                ata=ata,
                item_generico=item_generico,
                marca=random.choice(marcas),
                quantidade_licitada=quantidade_licitada,
                valor_unitario=valor_unitario,
            )
            itens_ata.append(item_ata)
            total_ata += quantidade_licitada * valor_unitario
        ata.ata_saldo_total = limitar_valor_monetario(total_ata)
        ata.save(update_fields=['ata_saldo_total'])
    return itens_ata


def seed_empenhos(atas):
    return [
        Empenho.objects.create(
            codigo=formatar_codigo_empenho(numero=indice + 1, ano=ANO_REFERENCIA),
            ata=ata,
            valor_total=Decimal('0.00'),
            saldo_utilizado=Decimal('0.00'),
        )
        for indice, ata in enumerate(atas)
    ]


def _quantidade_inicial(item_ata):
    percentual = Decimal(random.randint(PCT_EMPENHO_MIN, PCT_EMPENHO_MAX)) / Decimal('100')
    quantidade = arredondar_quantidade_por_unidade(
        item_ata.quantidade_licitada * percentual,
        item_ata.item_generico.unidade_medida,
        permitir_zero=False,
    )
    return min(max(quantidade, Decimal('2.00')), item_ata.quantidade_licitada)


def seed_itens_empenho(empenhos):
    itens_empenho = []
    for empenho in empenhos:
        for item_ata in ItemAta.objects.filter(ata=empenho.ata).select_related('item_generico'):
            itens_empenho.append(
                ItemEmpenho.objects.create(
                    empenho=empenho,
                    item_ata=item_ata,
                    quantidade_atual=Decimal('0.00'),
                    quantidade_entrege=Decimal('0.00'),
                )
            )
    return itens_empenho


def seed_operacoes_item(itens_empenho):
    operacoes = []
    agora = timezone.now()
    for indice, item_empenho in enumerate(itens_empenho):
        item_ata = item_empenho.item_ata
        quantidade_inicial = _quantidade_inicial(item_ata)
        operacoes.append(
            registrar_operacao_item(
                item_empenho_id=item_empenho.id,
                tipo='inc',
                valor=quantidade_inicial,
                data=agora - timedelta(days=30 + indice % 15),
            )
        )
        item_empenho.refresh_from_db()
        if indice % 2 == 0:
            disponivel = item_ata.quantidade_licitada - item_empenho.quantidade_atual
            reforco = arredondar_quantidade_por_unidade(
                item_empenho.quantidade_atual * Decimal('0.10'),
                item_ata.item_generico.unidade_medida,
                permitir_zero=False,
            )
            reforco = min(reforco, disponivel)
            if reforco >= Decimal('1.00'):
                operacoes.append(
                    registrar_operacao_item(
                        item_empenho_id=item_empenho.id,
                        tipo='ref',
                        valor=reforco,
                        data=agora - timedelta(days=15 + indice % 10),
                    )
                )
                operacoes.append(
                    registrar_operacao_item(
                        item_empenho_id=item_empenho.id,
                        tipo='anl',
                        valor=reforco,
                        data=agora - timedelta(days=7 + indice % 5),
                    )
                )
                item_empenho.refresh_from_db()
    return operacoes


def seed_ordens_entrega(empenhos, solicitante):
    ordens = []
    agora = timezone.now()
    for indice, empenho in enumerate(empenhos):
        data_emissao = agora - timedelta(days=30 - (indice % 12), hours=indice % 8)
        ordem = OrdemEntrega.objects.create(
            empenho=empenho,
            codigo=f'OE-{ANO_REFERENCIA}-{10000 + indice}',
            status='esp',
            data_entrega_prevista=data_emissao + timedelta(days=7 + indice % 5),
            data_entrega=None,
            valor_total_executado=Decimal('0.00'),
            solicitante=solicitante,
        )
        ordem.data_emissao = data_emissao
        ordem.save(update_fields=['data_emissao'])
        ordens.append(ordem)
    return ordens


def _quantidade_solicitada(item_empenho):
    unidade = item_empenho.item_ata.item_generico.unidade_medida
    metade = arredondar_quantidade_por_unidade(
        item_empenho.quantidade_atual / Decimal('2'),
        unidade,
        permitir_zero=False,
    )
    return min(max(metade, Decimal('2.00')), item_empenho.quantidade_atual)


def seed_itens_ordem(ordens):
    itens_ordem = []
    for ordem in ordens:
        itens_empenho = list(
            ItemEmpenho.objects.filter(empenho=ordem.empenho)
            .select_related('item_ata__item_generico')
            .order_by('id')
        )
        for item_empenho in itens_empenho:
            quantidade_solicitada = _quantidade_solicitada(item_empenho)
            if quantidade_solicitada <= Decimal('0.00'):
                continue
            item_ordem = ItemOrdem.objects.create(
                ordem_entrega=ordem,
                item_empenho=item_empenho,
                quantidade_solicitada=quantidade_solicitada,
                quantidade_entregue=Decimal('0.00'),
            )
            item_empenho.quantidade_atual -= quantidade_solicitada
            item_empenho.quantidade_entrege += quantidade_solicitada
            if item_empenho.quantidade_atual < Decimal('0.00'):
                raise RuntimeError('A reserva da ordem deixaria o item de empenho negativo.')
            item_empenho.save(update_fields=['quantidade_atual', 'quantidade_entrege'])
            itens_ordem.append(item_ordem)
    return itens_ordem


def _quantidade_parcial(item_ordem):
    unidade = item_ordem.item_empenho.item_ata.item_generico.unidade_medida
    quantidade = arredondar_quantidade_por_unidade(
        item_ordem.quantidade_solicitada / Decimal('2'),
        unidade,
        permitir_zero=False,
    )
    if quantidade >= item_ordem.quantidade_solicitada:
        quantidade = item_ordem.quantidade_solicitada - Decimal('1.00')
    if quantidade <= Decimal('0.00'):
        raise RuntimeError('Não foi possível gerar um recebimento parcial válido.')
    return quantidade


def _data_validade_lote_demo(*, catmat, sequencia, data_entrada, hoje):
    dias_por_situacao = (-3, 5, 20, 120)
    try:
        indice_situacao = (int(str(catmat)[-1]) + sequencia - 1) % len(dias_por_situacao)
    except (TypeError, ValueError):
        indice_situacao = (
            sum(ord(caractere) for caractere in f'{catmat}-{sequencia}')
            % len(dias_por_situacao)
        )
    data_validade = hoje + timedelta(days=dias_por_situacao[indice_situacao])
    if timezone.is_aware(data_entrada):
        data_recebimento = timezone.localtime(data_entrada, FUSO_ESTOQUE).date()
    else:
        data_recebimento = data_entrada.date()
    if data_validade < data_recebimento:
        data_validade = data_recebimento + timedelta(days=1)
    return data_validade


def _lotes_recebimento_demo(*, item_ordem, quantidade, data_entrada, dividir, hoje):
    item_generico = item_ordem.item_empenho.item_ata.item_generico
    catmat = item_generico.catmat
    unidade = item_generico.unidade_medida

    def criar_lote(sequencia, quantidade_lote):
        return {
            'numero_lote': f'DEMO-{catmat}-{sequencia:03d}',
            'data_validade': _data_validade_lote_demo(
                catmat=catmat,
                sequencia=sequencia,
                data_entrada=data_entrada,
                hoje=hoje,
            ),
            'quantidade': quantidade_lote,
        }

    if dividir:
        primeira_parcela = arredondar_quantidade_por_unidade(
            quantidade / Decimal('2'),
            unidade,
            permitir_zero=False,
        )
        segunda_parcela = quantidade - primeira_parcela
        if primeira_parcela > Decimal('0.000') and segunda_parcela > Decimal('0.000'):
            return [
                criar_lote(1, primeira_parcela),
                criar_lote(2, segunda_parcela),
            ]
    return [criar_lote(1, quantidade)]


def seed_recebimentos(ordens, estoquista):
    """Registra recebimentos reais para produzir cenários esp, par e con."""
    hoje = timezone.localtime(timezone.now(), FUSO_ESTOQUE).date()
    indice_item_recebimento = 0
    for indice, ordem in enumerate(ordens):
        cenario = ('con', 'par', 'esp')[indice % 3]
        if cenario == 'esp':
            continue
        data_entrada = ordem.data_emissao + timedelta(days=3 + indice % 4)
        itens_recebidos = []
        for item_ordem in ItemOrdem.objects.filter(ordem_entrega=ordem).select_related(
            'item_empenho__item_ata__item_generico'
        ):
            if cenario == 'con':
                quantidade = item_ordem.quantidade_solicitada
                observacao = ''
            else:
                quantidade = _quantidade_parcial(item_ordem)
                observacao = (
                    'Recebimento parcial de demonstração; fornecedor deverá complementar '
                    'a quantidade pendente.'
                )
            itens_recebidos.append(
                {
                    'item_ordem_id': item_ordem.id,
                    'lotes': _lotes_recebimento_demo(
                        item_ordem=item_ordem,
                        quantidade=quantidade,
                        data_entrada=data_entrada,
                        dividir=indice_item_recebimento % 2 == 0,
                        hoje=hoje,
                    ),
                    'observacao': observacao,
                }
            )
            indice_item_recebimento += 1
        if not itens_recebidos:
            raise RuntimeError('A ordem de demonstração não possui itens para receber.')
        registrar_recebimento(
            ordem_id=ordem.id,
            itens_recebidos=itens_recebidos,
            usuario=estoquista,
            data_entrada=data_entrada,
        )


def _lotes_carga_inicial_demo(*, dados, indice, data_carga):
    if timezone.is_aware(data_carga):
        data_local = timezone.localtime(data_carga, FUSO_ESTOQUE).date()
    else:
        data_local = data_carga.date()
    quantidade = Decimal(dados['quantidade']).quantize(Decimal('0.001'))

    def lote(sequencia, quantidade_lote, dias):
        return {
            'numero_lote': f"INI-{dados['catmat']}-{sequencia:03d}",
            'data_validade': data_local + timedelta(days=dias),
            'quantidade': quantidade_lote,
        }

    if indice % 2 == 0:
        primeira_parcela = (quantidade / Decimal('2')).quantize(
            Decimal('0.001'),
            rounding=ROUND_HALF_UP,
        )
        segunda_parcela = (quantidade - primeira_parcela).quantize(Decimal('0.001'))
        if primeira_parcela > Decimal('0.000') and segunda_parcela > Decimal('0.000'):
            return [
                lote(1, primeira_parcela, 120 + indice),
                lote(2, segunda_parcela, 240 + indice),
            ]
    return [lote(1, quantidade, 120 + indice)]


def seed_carga_inicial_estoque(estoquista):
    """Cadastra os gêneros só de estoque e registra a carga inicial de cada um."""
    data_carga = timezone.now()
    for indice, dados in enumerate(ITENS_CARGA_INICIAL):
        genero = ItemGenerico.objects.create(
            catmat=dados['catmat'],
            descricao=dados['descricao'],
            unidade_medida=dados['unidade'],
            categoria=dados['categoria'],
            conteudo_embalagem=dados['conteudo_embalagem'],
            unidade_embalagem=dados['unidade_embalagem'],
        )
        registrar_carga_inicial(
            item_generico_id=genero.id,
            lotes=_lotes_carga_inicial_demo(
                dados=dados,
                indice=indice,
                data_carga=data_carga,
            ),
            justificativa='Carga inicial de desenvolvimento do estoque físico do R.U.',
            usuario=estoquista,
            data_hora=data_carga,
        )
    return len(ITENS_CARGA_INICIAL)


def banco_possui_dados_de_dominio():
    modelos = (
        Endereco,
        Fornecedor,
        ItemGenerico,
        Licitacao,
        Ata,
        ItemAta,
        Empenho,
        ItemEmpenho,
        OperacaoItem,
        OrdemEntrega,
        ItemOrdem,
        Estoque,
        Inventario,
        ItemInventario,
        MovimentacaoEstoque,
    )
    return any(modelo.objects.exists() for modelo in modelos)


def clean_database():
    """Limpa apenas uma base descartável sem histórico protegido de estoque."""
    if (
        MovimentacaoEstoque.objects.exists()
        or Inventario.objects.exists()
        or ItemInventario.objects.exists()
        or Estoque.objects.exclude(saldo_atual=0).exists()
    ):
        raise RuntimeError(
            'Reset recusado: existe histórico de estoque protegido. Para recriar a demonstração, '
            'remova o volume MySQL somente em ambiente descartável ou use um banco novo.'
        )
    ItemOrdem.objects.all().delete()
    OrdemEntrega.objects.all().delete()
    OperacaoItem.objects.all().delete()
    ItemEmpenho.objects.all().delete()
    Empenho.objects.all().delete()
    ItemAta.objects.all().delete()
    Ata.objects.all().delete()
    Licitacao.objects.all().delete()
    Fornecedor.objects.all().delete()
    LoteEstoque.objects.all().delete()
    Estoque.objects.all().delete()
    ItemGenerico.objects.all().delete()
    Endereco.objects.all().delete()


def validar_seed():
    papeis_esperados = {
        'diretor': Papel.DIRETOR,
        'tecnico': Papel.TECNICO_ADMINISTRATIVO,
        'nutricionista': Papel.NUTRICIONISTA,
        'estoquista': Papel.ESTOQUISTA,
    }
    for username, papel in papeis_esperados.items():
        if not Usuario.objects.filter(username=username, papel=papel, is_active=True).exists():
            raise RuntimeError(f'Perfil obrigatório ausente ou inativo: {username}.')
    if Licitacao.objects.filter(atual=True).count() != 1:
        raise RuntimeError('A demonstração deve possuir exatamente uma licitação atual.')
    for item_generico in ItemGenerico.objects.all():
        if Estoque.objects.filter(item_generico=item_generico).count() != 1:
            raise RuntimeError(f'O item {item_generico.catmat} não possui exatamente um estoque.')
    for item_ordem in ItemOrdem.objects.select_related('ordem_entrega__empenho', 'item_empenho__empenho'):
        if item_ordem.ordem_entrega.empenho_id != item_ordem.item_empenho.empenho_id:
            raise RuntimeError('Item de ordem associado a empenho diferente do empenho da ordem.')
        if not Decimal('0.00') <= item_ordem.quantidade_entregue <= item_ordem.quantidade_solicitada:
            raise RuntimeError('Quantidade entregue fora do intervalo solicitado.')
    status_presentes = set(OrdemEntrega.objects.values_list('status', flat=True))
    if not {'esp', 'par', 'con'}.issubset(status_presentes):
        raise RuntimeError('A demonstração deve possuir ordens esp, par e con.')
    if not MovimentacaoEstoque.objects.exists() or not Estoque.objects.filter(saldo_atual__gt=0).exists():
        raise RuntimeError('A demonstração deve possuir movimentação e saldo positivo em estoque.')
    if not PendenciaFornecedor.objects.filter(status=PendenciaFornecedor.Status.ABERTA).exists():
        raise RuntimeError('A demonstração deve possuir ao menos uma pendência aberta de fornecedor.')
    tolerancia = Decimal('0.01')
    for item_empenho in ItemEmpenho.objects.all():
        saldo_operacional = sum(
            (
                operacao.valor
                if operacao.tipo in {'inc', 'ref'}
                else -operacao.valor
            )
            for operacao in OperacaoItem.objects.filter(item_empenho=item_empenho)
        )
        saldo_item = item_empenho.quantidade_atual + item_empenho.quantidade_entrege
        if abs(saldo_item - saldo_operacional) > tolerancia:
            raise RuntimeError('A equação financeira do item de empenho está inconsistente.')
    for empenho in Empenho.objects.all():
        if not Decimal('0.00') <= empenho.saldo_utilizado <= empenho.valor_total:
            raise RuntimeError('O saldo utilizado do empenho está inconsistente.')
    for estoque in Estoque.objects.select_related('item_generico'):
        lote_legado = LoteEstoque.objects.filter(
            estoque=estoque,
            numero_lote=LoteEstoque.NUMERO_LOTE_LEGADO,
        ).first()
        if lote_legado is not None and (
            not lote_legado.legado
            or lote_legado.data_validade is not None
        ):
            raise RuntimeError(
                f'Lote LEGADO inconsistente para {estoque.item_generico.descricao}.'
            )
        saldo_lotes = (
            LoteEstoque.objects.filter(estoque=estoque).aggregate(total=Sum('saldo_atual'))['total']
            or Decimal('0.000')
        ).quantize(Decimal('0.001'))
        saldo_consolidado = estoque.saldo_atual.quantize(Decimal('0.001'))
        if saldo_lotes != saldo_consolidado:
            raise RuntimeError(
                f'Estoque inconsistente para {estoque.item_generico.descricao}: '
                f'saldo consolidado = {saldo_consolidado}; saldo dos lotes = {saldo_lotes}.'
            )

    saldo_razao_estoques = {}
    saldo_razao_lotes = {}
    movimentos = MovimentacaoEstoque.objects.prefetch_related('alocacoes_lote__lote')
    for movimento in movimentos:
        alocacoes = list(movimento.alocacoes_lote.all())
        if not alocacoes:
            raise RuntimeError(f'Movimentação {movimento.id} não possui alocações de lote.')
        soma_alocacoes = sum(
            (alocacao.quantidade for alocacao in alocacoes),
            Decimal('0.000'),
        ).quantize(Decimal('0.001'))
        if soma_alocacoes != movimento.quantidade.quantize(Decimal('0.001')):
            raise RuntimeError(
                f'Movimentação {movimento.id} possui soma de alocações divergente.'
            )

        sinal = Decimal('1') if movimento.sentido == MovimentacaoEstoque.Sentido.ENTRADA else Decimal('-1')
        saldo_razao_estoques[movimento.estoque_id] = (
            saldo_razao_estoques.get(movimento.estoque_id, Decimal('0.000'))
            + sinal * movimento.quantidade
        )
        for alocacao in alocacoes:
            if alocacao.lote.estoque_id != movimento.estoque_id:
                raise RuntimeError(
                    f'Movimentação {movimento.id} possui lote de outro estoque.'
                )
            saldo_razao_lotes[alocacao.lote_id] = (
                saldo_razao_lotes.get(alocacao.lote_id, Decimal('0.000'))
                + sinal * alocacao.quantidade
            )

    for estoque in Estoque.objects.all():
        saldo_razao = saldo_razao_estoques.get(estoque.id, Decimal('0.000')).quantize(Decimal('0.001'))
        if saldo_razao != estoque.saldo_atual.quantize(Decimal('0.001')):
            raise RuntimeError(
                f'Livro-razão consolidado divergente para o estoque {estoque.id}.'
            )

    for lote in LoteEstoque.objects.all():
        saldo_razao = saldo_razao_lotes.get(lote.id, Decimal('0.000')).quantize(Decimal('0.001'))
        if saldo_razao != lote.saldo_atual.quantize(Decimal('0.001')):
            raise RuntimeError(f'Livro-razão divergente para o lote {lote.id}.')

    for movimento in MovimentacaoEstoque.objects.filter(
        tipo=MovimentacaoEstoque.Tipo.CARGA_INICIAL,
    ):
        alocacoes = MovimentacaoLote.objects.filter(movimentacao=movimento)
        if not alocacoes.exists() or alocacoes.filter(lote__legado=True).exists():
            raise RuntimeError(
                'Toda carga inicial deve possuir alocações em lotes reais.'
            )
    if Estoque.objects.filter(saldo_atual__lt=0).exists():
        raise RuntimeError('A demonstração não pode possuir saldo negativo em estoque.')
    if LoteEstoque.objects.filter(saldo_atual__lt=0).exists():
        raise RuntimeError('A demonstração não pode possuir saldo negativo em lote.')
    if not LoteEstoque.objects.filter(legado=False, saldo_atual__gt=0).exists():
        raise RuntimeError('A demonstração deve possuir ao menos um lote real com saldo positivo.')
    estoques_com_multiplos_lotes_reais = (
        LoteEstoque.objects
        .filter(legado=False, saldo_atual__gt=0)
        .values('estoque_id')
        .annotate(total=Count('id'))
        .filter(total__gte=2)
    )
    if not estoques_com_multiplos_lotes_reais.exists():
        raise RuntimeError(
            'A demonstração deve possuir ao menos um estoque com dois lotes reais positivos.'
        )


def imprimir_resumo():
    por_status = {
        status: OrdemEntrega.objects.filter(status=status).count()
        for status in ('esp', 'par', 'con')
    }
    print('\n✓ Seed concluído com sucesso!')
    print(f'  - Usuários: {Usuario.objects.count()}')
    print(f'  - Estoques: {Estoque.objects.count()}')
    print(f'  - Movimentações: {MovimentacaoEstoque.objects.count()}')
    print(f"  - Ordens esp/par/con: {por_status['esp']}/{por_status['par']}/{por_status['con']}")
    print(
        '  - Pendências abertas: '
        f'{PendenciaFornecedor.objects.filter(status=PendenciaFornecedor.Status.ABERTA).count()}'
    )


def seed_all():
    modo = os.environ.get('SIGE_SEED_MODE', 'if_empty').strip().lower()
    if modo not in {'skip', 'if_empty', 'refresh_demo'}:
        raise RuntimeError('SIGE_SEED_MODE inválido. Use skip, if_empty ou refresh_demo.')
    if modo == 'skip':
        print('Seed ignorada: SIGE_SEED_MODE=skip.')
        return
    validar_catalogo_seed()
    if modo == 'if_empty' and banco_possui_dados_de_dominio():
        print(
            'Banco já possui dados de domínio. A carga de demonstração não será reaplicada. '
            'Para recriar dados de desenvolvimento use SIGE_SEED_MODE=refresh_demo em um banco '
            'descartável ou recrie o volume MySQL.'
        )
        return
    with transaction.atomic():
        if modo == 'refresh_demo' and banco_possui_dados_de_dominio():
            clean_database()
        random.seed(SEED_RANDOM)
        print(f'Populando banco de dados com seed determinística {SEED_RANDOM}...')
        usuarios = create_usuarios()
        enderecos = seed_enderecos()
        fornecedores = seed_fornecedores(enderecos)
        itens_genericos = seed_itens_genericos()
        licitacoes_validas = seed_licitacoes()
        licitacoes_validas[0].definir_como_atual()
        licitacoes_expiradas = seed_licitacoes_expiradas()
        atas = seed_atas(licitacoes_validas + licitacoes_expiradas, fornecedores)
        itens_ata = seed_itens_ata(atas, itens_genericos)
        empenhos = seed_empenhos(atas)
        itens_empenho = seed_itens_empenho(empenhos)
        operacoes = seed_operacoes_item(itens_empenho)
        ordens = seed_ordens_entrega(empenhos, usuarios[Papel.TECNICO_ADMINISTRATIVO])
        itens_ordem = seed_itens_ordem(ordens)
        seed_recebimentos(ordens, usuarios[Papel.ESTOQUISTA])
        cargas_iniciais = seed_carga_inicial_estoque(usuarios[Papel.ESTOQUISTA])
        validar_seed()
    imprimir_resumo()
    return {
        'enderecos': len(enderecos),
        'fornecedores': len(fornecedores),
        'itens_genericos': len(itens_genericos),
        'licitacoes': len(licitacoes_validas) + len(licitacoes_expiradas),
        'atas': len(atas),
        'itens_ata': len(itens_ata),
        'empenhos': len(empenhos),
        'itens_empenho': len(itens_empenho),
        'operacoes': len(operacoes),
        'ordens': len(ordens),
        'itens_ordem': len(itens_ordem),
        'cargas_iniciais': cargas_iniciais,
    }


if __name__ == '__main__':
    if '--validate-catalog' in sys.argv:
        validar_catalogo_seed()
        print('Catálogo da seed válido.')
    else:
        seed_all()
