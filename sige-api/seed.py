import os
import random
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sige_api.settings')
import django
django.setup()

from cadastro.models import Endereco, Fornecedor, ItemGenerico
from licitacao.models import Licitacao, Ata, ItemAta
from empenho.models import Empenho, ItemEmpenho, OperacaoItem
from entrega.models import OrdemEntrega, ItemOrdem

def seed_enderecos(n=5):
    enderecos = []
    for i in range(n):
        endereco = Endereco.objects.create(
            lagradouro=f"Rua {i}",
            numero=str(random.randint(1, 999)),
            bairro=f"Bairro {i}",
            cep=f"{random.randint(10000000,99999999)}",
            municipio=f"Município {i}",
            estado=random.choice(['SP', 'RJ', 'MG', 'RS'])
        )
        enderecos.append(endereco)
    return enderecos

def seed_fornecedores(n=5, enderecos=None):
    fornecedores = []
    for i in range(n):
        fornecedor = Fornecedor.objects.create(
            razao_social=f"Fornecedor {i}",
            nome_fantasia=f"Fantasia {i}",
            cnpj=f"{random.randint(10,99)}.{random.randint(100,999)}.{random.randint(100,999)}/0001-{random.randint(10,99)}",
            telefone=f"({random.randint(10,99)}) {random.randint(10000,99999)}-{random.randint(1000,9999)}",
            email=f"fornecedor{i}@exemplo.com",
            endereco=random.choice(enderecos)
        )
        fornecedores.append(fornecedor)
    return fornecedores

def seed_itens_genericos(n=5):
    categorias = ['SM', 'Lac', 'Oli', 'Fr', 'Le', 'Pr']
    unidades = ['KG', 'L', 'un', 'PCT', 'CX']
    itens = []
    for i in range(n):
        item = ItemGenerico.objects.create(
            catmat=f"{random.randint(100000,999999)}",
            descricao=f"Item {i}",
            unidade_medida=random.choice(unidades),
            categoria=random.choice(categorias)
        )
        itens.append(item)
    return itens

def seed_licitacoes(n=3):
    licitacoes = []
    for i in range(n):
        licitacao = Licitacao.objects.create(
            numero_licitacao=f"LIC{i+1:03d}",
            validade=random.randint(6,24),
            data_abertura=datetime.now().date() - timedelta(days=random.randint(0,365)),
            descricao=f"Descrição da Licitação {i}"
        )
        licitacoes.append(licitacao)
    return licitacoes

def seed_atas(n=5, licitacoes=None, fornecedores=None):
    atas = []
    pares_usados = set()
    for i in range(n):
        while True:
            licitacao = random.choice(licitacoes)
            fornecedor = random.choice(fornecedores)
            par = (licitacao.id, fornecedor.id)
            if par not in pares_usados:
                pares_usados.add(par)
                break
        ata = Ata.objects.create(
            numero_ata=f"ATA{i+1:03d}",
            ata_saldo_total=random.uniform(1000,5000),
            licitacao=licitacao,
            fornecedor=fornecedor
        )
        atas.append(ata)
    return atas

def seed_itens_ata(n=10, atas=None, itens_genericos=None):
    itens_ata = []
    for i in range(n):
        item_ata = ItemAta.objects.create(
            ata=random.choice(atas),
            item_generico=random.choice(itens_genericos),
            marca=f"Marca {i}",
            quantidade_licitada=random.uniform(10,100),
            valor_unitario=random.uniform(1,20)
        )
        itens_ata.append(item_ata)
    return itens_ata

def seed_empenhos(n=5, atas=None):
    empenhos = []
    for i in range(n):
        empenho = Empenho.objects.create(
            codigo=f"EMP{i+1:03d}",
            ata=random.choice(atas),
            valor_total=random.uniform(500,2000),
            saldo_utilizado=random.uniform(0,500)
        )
        empenhos.append(empenho)
    return empenhos

def seed_itens_empenho(n=10, empenhos=None, itens_ata=None):
    itens_empenho = []
    for i in range(n):
        item_empenho = ItemEmpenho.objects.create(
            empenho=random.choice(empenhos),
            item_ata=random.choice(itens_ata),
            quantidade_atual=random.uniform(1,50)
        )
        itens_empenho.append(item_empenho)
    return itens_empenho

def seed_operacoes_item(n=10, itens_empenho=None):
    tipos = ['inc', 'ref', 'anl']
    operacoes = []
    for i in range(n):
        operacao = OperacaoItem.objects.create(
            item_empenho=random.choice(itens_empenho),
            tipo=random.choice(tipos),
            valor=random.uniform(10,100),
            data=datetime.now().date() - timedelta(days=random.randint(0,30))
        )
        operacoes.append(operacao)
    return operacoes

def seed_ordens_entrega(n=5, empenhos=None):
    ordens = []
    for i in range(n):
        ordem = OrdemEntrega.objects.create(
            empenho=random.choice(empenhos),
            codigo=f"OE{i+1:03d}",
            status=random.choice(['esp', 'con']),
            valor_total_executado=random.uniform(100,1000)
        )
        ordens.append(ordem)
    return ordens

def seed_itens_ordem(n=10, ordens=None, itens_empenho=None):
    itens_ordem = []
    for i in range(n):
        item_ordem = ItemOrdem.objects.create(
            ordem_entrega=random.choice(ordens),
            item_empenho=random.choice(itens_empenho),
            quantidade_solicitada=random.uniform(1,20),
            quantidade_entregue=random.uniform(0,20),
            observacao=f"Observação {i}"
        )
        itens_ordem.append(item_ordem)
    return itens_ordem
def clean_database():
    print("Limpando o banco...")
    ItemOrdem.objects.all().delete()
    OrdemEntrega.objects.all().delete()
    OperacaoItem.objects.all().delete()
    ItemEmpenho.objects.all().delete()
    Empenho.objects.all().delete()
    ItemAta.objects.all().delete()
    Ata.objects.all().delete()
    Licitacao.objects.all().delete()
    Fornecedor.objects.all().delete()
    ItemGenerico.objects.all().delete()
    Endereco.objects.all().delete()
    print("Banco limpo!")
def seed_all():
    clean_database()
    enderecos = seed_enderecos()
    fornecedores = seed_fornecedores(enderecos=enderecos)
    itens_genericos = seed_itens_genericos()
    licitacoes = seed_licitacoes()
    atas = seed_atas(licitacoes=licitacoes, fornecedores=fornecedores)
    itens_ata = seed_itens_ata(atas=atas, itens_genericos=itens_genericos)
    empenhos = seed_empenhos(atas=atas)
    itens_empenho = seed_itens_empenho(empenhos=empenhos, itens_ata=itens_ata)
    operacoes = seed_operacoes_item(itens_empenho=itens_empenho)
    ordens = seed_ordens_entrega(empenhos=empenhos)
    itens_ordem = seed_itens_ordem(ordens=ordens, itens_empenho=itens_empenho)
    print("Seed concluído com sucesso!")

if __name__ == "__main__":
    seed_all()