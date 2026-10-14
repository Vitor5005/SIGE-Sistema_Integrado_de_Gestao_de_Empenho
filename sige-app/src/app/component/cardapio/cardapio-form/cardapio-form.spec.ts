import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap, Router } from '@angular/router';
import { of } from 'rxjs';
import { vi } from 'vitest';

import { DisponibilidadeGenero } from '../../../model/cardapio';
import { CardapioService } from '../../../service/cardapio.service';
import { SolicitacaoReforcoService } from '../../../service/solicitacao-reforco.service';
import { CardapioForm } from './cardapio-form';

describe('CardapioForm', () => {
  let component: CardapioForm;
  let fixture: ComponentFixture<CardapioForm>;
  let cardapioService: Record<string, ReturnType<typeof vi.fn>>;
  let reforcoService: Record<string, ReturnType<typeof vi.fn>>;

  const arroz: DisponibilidadeGenero = {
    item_generico_id: 1, catmat: '100001', descricao: 'Arroz', unidade_medida: 'KG', categoria: 'SM',
    conteudo_embalagem: null, unidade_embalagem: null, saldo_atual: 40, reservado: 15, disponivel: 25,
  };

  const sal: DisponibilidadeGenero = {
    ...arroz, item_generico_id: 2, catmat: '100002', descricao: 'Sal', saldo_atual: 0, reservado: 0, disponivel: 0,
  };

  beforeEach(async () => {
    cardapioService = {
      disponibilidade: vi.fn(() => of([sal, arroz])),
      obter: vi.fn(),
      salvar: vi.fn(() => of({ id: 7 })),
      enviar: vi.fn(() => of({ id: 7 })),
    };

    reforcoService = {
      opcoesPorGenero: vi.fn(() => of([
        {
          item_empenho: 9, empenho_id: 3, empenho_codigo: 'EMP-1', ata_numero: 'ATA-1', fornecedor: 'Fornecedor',
          unidade_medida: 'KG', quantidade_atual: '10.00', saldo_disponivel_ata: '40.00', possui_pedido_pendente: false,
        },
      ])),
      solicitar: vi.fn(() => of({ id: 1 })),
    };

    await TestBed.configureTestingModule({
      imports: [CardapioForm],
      providers: [
        { provide: CardapioService, useValue: cardapioService },
        { provide: SolicitacaoReforcoService, useValue: reforcoService },
        { provide: Router, useValue: { navigate: vi.fn() } },
        { provide: ActivatedRoute, useValue: { snapshot: { queryParamMap: convertToParamMap({}) } } },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(CardapioForm);
    component = fixture.componentInstance;
    component.ngOnInit();

    component.refeicao = 'JANTAR';
    component.estimativaPessoas = 550;
    component.preparacoes = 'ARROZ BRANCO';
  });

  it('libera o envio quando há saldo disponível', () => {
    component.secoes[0].linhas[0] = { item_generico: 1, quantidade: 25, observacao: '' };

    expect(component.excedeSaldo(1)).toBe(false);
    expect(component.podeEnviar).toBe(true);
  });

  it('bloqueia o envio quando o gênero passa do saldo disponível, somando todas as linhas', () => {
    component.secoes[0].linhas = [
      { item_generico: 1, quantidade: 20, observacao: 'p/ o arroz' },
      { item_generico: 1, quantidade: 10, observacao: 'p/ o feijão' },
    ];

    expect(component.totalPlanejado(1)).toBe(30);
    expect(component.excedeSaldo(1)).toBe(true);
    expect(component.generosSemSaldo.map((g) => g.descricao)).toEqual(['Arroz']);
    expect(component.podeEnviar).toBe(false);
    expect(component.podeSalvar).toBe(false);
  });

  it('reduz ao saldo disponível a quantidade que passa do limite', () => {
    const linha = { item_generico: 1, quantidade: 40, observacao: '' };
    component.secoes[0].linhas[0] = linha;

    component.ajustarAoSaldo(linha);

    expect(linha.quantidade).toBe(25);
    expect(component.foiAjustada(linha)).toBe(true);
  });

  it('considera as outras linhas do mesmo gênero no limite da linha', () => {
    const primeira = { item_generico: 1, quantidade: 20, observacao: '' };
    const segunda = { item_generico: 1, quantidade: 10, observacao: '' };
    component.secoes[0].linhas = [primeira, segunda];

    expect(component.maximoDaLinha(segunda)).toBe(5);
    component.ajustarAoSaldo(segunda);
    expect(segunda.quantidade).toBe(5);
  });

  it('não permite salvar com gênero zerado e lista os zerados por último', () => {
    expect(component.disponibilidade.map((g) => g.descricao)).toEqual(['Arroz', 'Sal']);

    component.secoes[0].linhas[0] = { item_generico: 2, quantidade: 1, observacao: '' };

    expect(component.generoSemSaldo(2)).toBe(true);
    expect(component.podeSalvar).toBe(false);
  });

  it('avisa estoque baixo quando sobra menos de 20% do disponível', () => {
    component.secoes[0].linhas[0] = { item_generico: 1, quantidade: 15, observacao: '' };
    expect(component.estoqueBaixo(1)).toBe(false);

    component.secoes[0].linhas[0].quantidade = 21;
    expect(component.estoqueBaixo(1)).toBe(true);
    expect(component.restanteAposCardapio(1)).toBe(4);
  });

  it('não permite salvar sem gêneros no detalhamento', () => {
    expect(component.itensPreenchidos.length).toBe(0);
    expect(component.podeSalvar).toBe(false);
  });

  it('exige título nas seções adicionais preenchidas', () => {
    component.secoes[0].linhas[0] = { item_generico: 1, quantidade: 5, observacao: '' };
    component.adicionarSecao();
    component.secoes[1].linhas[0] = { item_generico: 1, quantidade: 1, observacao: '' };

    expect(component.detalhamentoValido).toBe(false);

    component.secoes[1].titulo = 'SOBREMESA: FRUTA';
    expect(component.detalhamentoValido).toBe(true);
  });

  it('monta os itens com a seção e a ordem do detalhamento', () => {
    component.secoes[0].linhas[0] = { item_generico: 1, quantidade: 5, observacao: ' Cortar ' };
    component.salvarRascunho();

    const enviado = cardapioService['salvar'].mock.calls[0][0];
    expect(enviado.itens).toEqual([
      { ordem: 0, secao: '', item_generico: 1, quantidade_planejada: 5, observacao: 'Cortar' },
    ]);
  });

  it('pede reforço ao Diretor a partir de um gênero com estoque baixo', () => {
    const linha = { item_generico: 1, quantidade: 22, observacao: '' };
    component.secoes[0].linhas[0] = linha;
    expect(component.estoqueBaixo(1)).toBe(true);

    component.abrirReforco(linha);
    expect(component.reforco?.itemEmpenho).toBe(9);
    expect(component.reforco?.justificativa).toContain('restarão 3 KG');

    component.reforco!.quantidade = 50;
    expect(component.pedidoReforcoValido).toBe(false); // acima do saldo da ARP

    component.reforco!.quantidade = 30;
    component.enviarReforco();
    expect(reforcoService['solicitar']).toHaveBeenCalledWith(9, 30, expect.stringContaining('Arroz'));
    expect(component.reforco).toBeNull();
  });
});
