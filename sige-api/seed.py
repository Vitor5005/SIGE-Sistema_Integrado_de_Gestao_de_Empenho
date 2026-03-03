import os
import random
from datetime import datetime, timedelta
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sige_api.settings')
import django
django.setup()

from cadastro.models import Endereco, Fornecedor, ItemGenerico
from licitacao.models import Licitacao, Ata, ItemAta
from empenho.models import Empenho, ItemEmpenho, OperacaoItem
from entrega.models import OrdemEntrega, ItemOrdem

MAX_VALOR_MONETARIO = Decimal("1000000.00")
QTD_LICITADA_MIN = 20
QTD_LICITADA_MAX = 120
PCT_EMPENHO_MIN = 5
PCT_EMPENHO_MAX = 30
PCT_ENTREGA_CONCLUIDA_MIN = 85
PCT_ENTREGA_CONCLUIDA_MAX = 100
PCT_ENTREGA_ESPERA_MIN = 0
PCT_ENTREGA_ESPERA_MAX = 60


def limitar_valor_monetario(valor: Decimal) -> Decimal:
    return min(valor.quantize(Decimal("0.01")), MAX_VALOR_MONETARIO)

# Dados realistas para o contexto de um restaurante universitário
NOMES_FORNECEDORES = [
    {"razao": "ALIMENTOS NATURAIS LTDA", "fantasia": "Alimentos Naturais"},
    {"razao": "DISTRIBUIDORA DE ALIMENTOS JB", "fantasia": "Dist. JB"},
    {"razao": "FORNECEDORA DE CARNES PREMIUM", "fantasia": "Carnes Premium"},
    {"razao": "FRUTAS E VERDURAS DO ACRE", "fantasia": "Frutas & Verduras"},
    {"razao": "LATICÍNIOS DO BRASIL LTDA", "fantasia": "Laticínios Brasil"},
    {"razao": "PRODUTOS SECOS E MERCEARIA", "fantasia": "Mercearia Central"},
    {"razao": "DISTRIBUIDORA DE CONGELADOS", "fantasia": "Congelados Ltda"},
    {"razao": "FORNECEDORA DE BEBIDAS SA", "fantasia": "Bebidas Select"},
]

ENDERECOS = [
    {"logradouro": "Rua do Comércio", "numero": "123", "bairro": "Centro", "municipio": "Rio Branco", "estado": "AC", "cep": "69900000"},
    {"logradouro": "Avenida Getúlio Vargas", "numero": "456", "bairro": "Bosque", "municipio": "Rio Branco", "estado": "AC", "cep": "69900100"},
    {"logradouro": "Rua 6 de Agosto", "numero": "789", "bairro": "Centro", "municipio": "Rio Branco", "estado": "AC", "cep": "69900200"},
    {"logradouro": "Avenida Brasil", "numero": "321", "bairro": "Distrito Industrial", "municipio": "Rio Branco", "estado": "AC", "cep": "69920000"},
    {"logradouro": "Rua Rui Barbosa", "numero": "654", "bairro": "Taquari", "municipio": "Rio Branco", "estado": "AC", "cep": "69903000"},
]

ITENS_ALIMENTOS = [
    # Secos / Mercearia (SM)
    {"catmat": "100001", "descricao": "Arroz Integral 5kg", "categoria": "SM", "unidade": "KG"},
    {"catmat": "100002", "descricao": "Feijão Carioca 1kg", "categoria": "SM", "unidade": "KG"},
    {"catmat": "100003", "descricao": "Macarrão Integral 500g", "categoria": "SM", "unidade": "G"},
    {"catmat": "100004", "descricao": "Açúcar Cristal 1kg", "categoria": "SM", "unidade": "KG"},
    {"catmat": "100005", "descricao": "Sal Refinado 1kg", "categoria": "SM", "unidade": "KG"},
    # Lácteos (Lac)
    {"catmat": "200001", "descricao": "Leite Integral 1L", "categoria": "Lac", "unidade": "L"},
    {"catmat": "200002", "descricao": "Queijo Meia Cura 500g", "categoria": "Lac", "unidade": "G"},
    {"catmat": "200003", "descricao": "Iogurte Natural 500ml", "categoria": "Lac", "unidade": "mL"},
    {"catmat": "200004", "descricao": "Manteiga 200g", "categoria": "Lac", "unidade": "G"},
    # Óleos e Azeites (Oli)
    {"catmat": "300001", "descricao": "Óleo de Soja 900ml", "categoria": "Oli", "unidade": "mL"},
    {"catmat": "300002", "descricao": "Azeite Extra Virgem 500ml", "categoria": "Oli", "unidade": "mL"},
    {"catmat": "300003", "descricao": "Vinagre Branco 750ml", "categoria": "Oli", "unidade": "mL"},
    # Frutas (Fr)
    {"catmat": "400001", "descricao": "Banana Prata kg", "categoria": "Fr", "unidade": "KG"},
    {"catmat": "400002", "descricao": "Maçã Gala kg", "categoria": "Fr", "unidade": "KG"},
    {"catmat": "400003", "descricao": "Laranja Pera kg", "categoria": "Fr", "unidade": "KG"},
    # Legumes (Le)
    {"catmat": "500001", "descricao": "Alface Crespa kg", "categoria": "Le", "unidade": "KG"},
    {"catmat": "500002", "descricao": "Tomate kg", "categoria": "Le", "unidade": "KG"},
    {"catmat": "500003", "descricao": "Cebola kg", "categoria": "Le", "unidade": "KG"},
    {"catmat": "500004", "descricao": "Batata Doce kg", "categoria": "Le", "unidade": "KG"},
    # Proteínas (Pr)
    {"catmat": "600001", "descricao": "Frango Congelado kg", "categoria": "Pr", "unidade": "KG"},
    {"catmat": "600002", "descricao": "Carne Bovina kg", "categoria": "Pr", "unidade": "KG"},
    {"catmat": "600003", "descricao": "Ovos Caipira Dúzia", "categoria": "Pr", "unidade": "duzia"},
]

def seed_enderecos():
    """Cria endereços com dados realistas"""
    enderecos = []
    for endereco_data in ENDERECOS:
        cep = ''.join(char for char in endereco_data["cep"] if char.isdigit())[:8]
        endereco = Endereco.objects.create(
            lagradouro=endereco_data["logradouro"],
            numero=endereco_data["numero"],
            bairro=endereco_data["bairro"],
            cep=cep,
            municipio=endereco_data["municipio"],
            estado=endereco_data["estado"]
        )
        enderecos.append(endereco)
    return enderecos

def seed_fornecedores(enderecos=None):
    """Cria fornecedores com dados realistas"""
    fornecedores = []
    for i, fornecedor_data in enumerate(NOMES_FORNECEDORES):
        fornecedor = Fornecedor.objects.create(
            razao_social=fornecedor_data["razao"],
            nome_fantasia=fornecedor_data["fantasia"],
            cnpj=f"{random.randint(10,99)}.{random.randint(100,999)}.{random.randint(100,999)}/0001-{random.randint(10,99)}",
            telefone=f"({random.randint(61,99)}) {random.randint(98000,99999)}-{random.randint(1000,9999)}",
            email=f"contato{i}@{fornecedor_data['fantasia'].lower().replace(' ', '')}.com.br",
            endereco=random.choice(enderecos)
        )
        fornecedores.append(fornecedor)
    return fornecedores

def seed_itens_genericos():
    """Cria itens genéricos com dados realistas"""
    itens = []
    for item_data in ITENS_ALIMENTOS:
        item = ItemGenerico.objects.create(
            catmat=item_data["catmat"],
            descricao=item_data["descricao"],
            unidade_medida=item_data["unidade"],
            categoria=item_data["categoria"]
        )
        itens.append(item)
    return itens


def seed_licitacoes(n=3):
    """Cria licitações com datas realistas"""
    licitacoes = []
    for i in range(n):
        licitacao = Licitacao.objects.create(
            numero_licitacao=f"LIC-2026-{1000+i}",
            validade=random.randint(12, 24),  # Entre 12 e 24 meses
            data_abertura=datetime.now().date() - timedelta(days=random.randint(30, 180)),
            descricao=f"Licicitação para aquisição de produtos alimentícios lote {i+1}"
        )
        licitacoes.append(licitacao)
    return licitacoes

def seed_atas(licitacoes=None, fornecedores=None):
    atas = []
    for licitacao in licitacoes:
        fornecedores_sorteados = random.sample(fornecedores, k=min(2, len(fornecedores)))
        for fornecedor in fornecedores_sorteados:
            ata = Ata.objects.create(
                numero_ata=f"ATA-{licitacao.numero_licitacao}-{fornecedor.id}",
                ata_saldo_total=Decimal("0.00"), # Começa zerado
                licitacao=licitacao,
                fornecedor=fornecedor
            )
            atas.append(ata)
    return atas

def seed_itens_ata(atas=None, itens_genericos=None):
    marcas = ["Premium", "Padrão", "Integral", "Orgânico"]
    itens_ata_criados = []
    for ata in atas:
        total_acumulado = Decimal("0.00")
        num_itens = random.randint(3, 8)
        itens_sorteados = random.sample(itens_genericos, k=min(num_itens, len(itens_genericos)))
        
        for item_generico in itens_sorteados:
            qtd = Decimal(random.randint(QTD_LICITADA_MIN, QTD_LICITADA_MAX))
            valor_uni = Decimal(random.randint(10, 100)) + Decimal(random.randint(0, 99)) / 100
            
            item_ata = ItemAta.objects.create(
                ata=ata,
                item_generico=item_generico,
                marca=random.choice(marcas),
                quantidade_licitada=qtd,
                valor_unitario=valor_uni
            )
            itens_ata_criados.append(item_ata)
            total_acumulado += (qtd * valor_uni)
        
        # ATUALIZAÇÃO CRUCIAL: O saldo da ata é a soma dos itens
        ata.ata_saldo_total = limitar_valor_monetario(total_acumulado)
        ata.save()

    return itens_ata_criados


def seed_empenhos(atas=None):
    empenhos = []
    for i, ata in enumerate(atas):
        empenho = Empenho.objects.create(
            codigo=f"EMP-2026-{10000+i}",
            ata=ata,
            valor_total=Decimal("0.00"), # Será calculado pelos itens
            saldo_utilizado=Decimal("0.00")
        )
        empenhos.append(empenho)
    return empenhos

def seed_itens_empenho(empenhos=None, itens_ata=None):
    itens_empenho_criados = []
    empenhos_sem_uso = []

    for empenho in empenhos:
        itens_da_ata = ItemAta.objects.filter(ata=empenho.ata)
        if not itens_da_ata.exists():
            continue

        valor_empenhado_total = Decimal("0.00")
        
        # Empenhamos alguns itens daquela Ata
        for item_ata in random.sample(list(itens_da_ata), k=random.randint(1, len(itens_da_ata))):
            # Quantidade empenhada nunca maior que a licitada
            qtd_empenhada = item_ata.quantidade_licitada * Decimal(random.randint(PCT_EMPENHO_MIN, PCT_EMPENHO_MAX)) / Decimal(100)
            
            item_empenho = ItemEmpenho.objects.create(
                empenho=empenho,
                item_ata=item_ata,
                quantidade_atual=qtd_empenhada
            )
            itens_empenho_criados.append(item_empenho)
            valor_empenhado_total += (qtd_empenhada * item_ata.valor_unitario)
            
        # Atualiza o valor total do empenho com a soma real
        empenho.valor_total = limitar_valor_monetario(valor_empenhado_total)

        # Regra de negócio: saldo utilizado não pode ultrapassar
        # o somatório de (valor_unitario * quantidade_atual) dos itens empenhados.
        limite_utilizavel = empenho.valor_total

        # Parte dos empenhos fica sem utilização para cenário realista
        if random.random() < 0.35:
            empenho.saldo_utilizado = Decimal("0.00")
            empenhos_sem_uso.append(empenho)
        else:
            percentual_utilizado = Decimal(random.randint(1, 95)) / Decimal(100)
            valor_utilizado = (limite_utilizavel * percentual_utilizado).quantize(Decimal("0.01"))
            empenho.saldo_utilizado = min(limitar_valor_monetario(valor_utilizado), limite_utilizavel)

        empenho.save()

    # Garante ao menos um empenho não utilizado (quando houver empenhos)
    if empenhos and not empenhos_sem_uso:
        empenho_sorteado = random.choice(empenhos)
        empenho_sorteado.saldo_utilizado = Decimal("0.00")
        empenho_sorteado.save(update_fields=["saldo_utilizado"])

    return itens_empenho_criados

def seed_operacoes_item(itens_empenho=None):
    """
    Cria operações de empenho com:
    - Tipos válidos: inc (inclusão), ref (reforço), anl (anulação)
    - Uma a três operações por item de empenho
    - Valores coerentes
    """
    tipos_operacao = ['inc', 'ref', 'anl']
    operacoes = []
    
    for item_empenho in itens_empenho:
        # 1 a 3 operações por item
        num_operacoes = random.randint(1, 3)
        
        for j in range(num_operacoes):
            tipo = random.choice(tipos_operacao)
            # Valor relacionado à quantidade e valor unitário
            valor_max = float(item_empenho.item_ata.valor_unitario) * 20
            valor = Decimal(random.randint(10, int(valor_max) if valor_max > 10 else 50))
            
            operacao = OperacaoItem.objects.create(
                item_empenho=item_empenho,
                tipo=tipo,
                valor=limitar_valor_monetario(valor),
                data=datetime.now().date() - timedelta(days=random.randint(0, 60))
            )
            operacoes.append(operacao)
    return operacoes


def seed_ordens_entrega(empenhos=None):
    """
    Cria ordens de entrega com:
    - Uma a duas ordens por empenho
    - Status realista
    - Datas coerentes (entrega >= emissão)
    """
    ordens = []
    
    for i, empenho in enumerate(empenhos):
        # 1 a 2 ordens por empenho
        num_ordens = random.randint(1, 2)
        
        for j in range(num_ordens):
            status = random.choice(['esp', 'con'])
            data_emissao = datetime.now().date() - timedelta(days=random.randint(1, 30))
            
            # Data de entrega só existe se status é 'con'
            data_entrega = None
            if status == 'con':
                data_entrega = data_emissao + timedelta(days=random.randint(1, 10))
            
            ordem = OrdemEntrega.objects.create(
                empenho=empenho,
                codigo=f"OE-2026-{10000 + i*2 + j}",
                status=status,
                data_entrega=data_entrega,
                valor_total_executado=limitar_valor_monetario(
                    empenho.valor_total * Decimal(random.randint(50, 100)) / Decimal(100)
                )
            )
            ordens.append(ordem)
    return ordens

def seed_itens_ordem(ordens=None, itens_empenho=None):
    """
    Cria itens de ordem com validações:
    - quantidade_entregue <= quantidade_solicitada
    - Se status da ordem é 'con', quantidade_entregue > 0
    - Se status é 'esp', quantidade_entregue pode ser 0
    """
    itens_ordem = []
    
    for ordem in ordens:
        # 1 a 3 itens por ordem
        num_itens = min(random.randint(1, 3), len(itens_empenho))
        itens_sorteados = random.sample(itens_empenho, k=num_itens)
        
        for item_empenho in itens_sorteados:
            quantidade_solicitada = item_empenho.quantidade_atual
            
            # Se ordem está concluída, deve ter entregado pelo menos 85%
            if ordem.status == 'con':
                taxa_entrega = Decimal(random.randint(PCT_ENTREGA_CONCLUIDA_MIN, PCT_ENTREGA_CONCLUIDA_MAX)) / Decimal(100)
            else:
                # Se em espera, pode ter entregado de 0% a 60%
                taxa_entrega = Decimal(random.randint(PCT_ENTREGA_ESPERA_MIN, PCT_ENTREGA_ESPERA_MAX)) / Decimal(100)
            
            quantidade_entregue = quantidade_solicitada * taxa_entrega
            observacao = None
            
            # Se não entregou tudo, adiciona observação
            if quantidade_entregue < quantidade_solicitada:
                observacao = "Entrega parcial pendente"
            
            item_ordem = ItemOrdem.objects.create(
                ordem_entrega=ordem,
                item_empenho=item_empenho,
                quantidade_solicitada=quantidade_solicitada,
                quantidade_entregue=quantidade_entregue,
                observacao=observacao
            )
            itens_ordem.append(item_ordem)
    return itens_ordem


def clean_database():
    """Limpa todas as tabelas na ordem correta (respeitando foreign keys)"""
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
    print("✓ Banco limpo com sucesso!")

def seed_all():
    """Executa todas as funções de seed na ordem correta"""
    clean_database()
    
    print("Populando banco de dados...")
    print("  → Criando endereços...")
    enderecos = seed_enderecos()
    
    print("  → Criando fornecedores...")
    fornecedores = seed_fornecedores(enderecos=enderecos)
    
    print("  → Criando itens genéricos...")
    itens_genericos = seed_itens_genericos()
    
    print("  → Criando licitações...")
    licitacoes = seed_licitacoes()
    
    print("  → Criando atas...")
    atas = seed_atas(licitacoes=licitacoes, fornecedores=fornecedores)
    
    print("  → Criando itens de ata...")
    itens_ata = seed_itens_ata(atas=atas, itens_genericos=itens_genericos)
    
    print("  → Criando empenhos...")
    empenhos = seed_empenhos(atas=atas)
    
    print("  → Criando itens de empenho...")
    itens_empenho = seed_itens_empenho(empenhos=empenhos, itens_ata=itens_ata)
    
    print("  → Criando operações de item...")
    operacoes = seed_operacoes_item(itens_empenho=itens_empenho)
    
    print("  → Criando ordens de entrega...")
    ordens = seed_ordens_entrega(empenhos=empenhos)
    
    print("  → Criando itens de ordem...")
    itens_ordem = seed_itens_ordem(ordens=ordens, itens_empenho=itens_empenho)
    
    print("\n✓ Seed concluído com sucesso!")
    print(f"  - {len(enderecos)} endereços criados")
    print(f"  - {len(fornecedores)} fornecedores criados")
    print(f"  - {len(itens_genericos)} itens genéricos criados")
    print(f"  - {len(licitacoes)} licitações criadas")
    print(f"  - {len(atas)} atas criadas")
    print(f"  - {len(itens_ata)} itens de ata criados")
    print(f"  - {len(empenhos)} empenhos criados")
    print(f"  - {len(itens_empenho)} itens de empenho criados")
    print(f"  - {len(operacoes)} operações de item criadas")
    print(f"  - {len(ordens)} ordens de entrega criadas")
    print(f"  - {len(itens_ordem)} itens de ordem criados")

if __name__ == "__main__":
    seed_all()