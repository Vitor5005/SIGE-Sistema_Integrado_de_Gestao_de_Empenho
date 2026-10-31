import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap, provideRouter, Router } from '@angular/router';
import { of, Subject } from 'rxjs';
import { vi } from 'vitest';

import { DisponibilidadeGenero } from '../../../model/cardapio';
import { environment } from '../../../environments/environment';
import { CardapioService } from '../../../service/cardapio.service';
import { SolicitacaoReforcoService } from '../../../service/solicitacao-reforco.service';
import { CardapioForm } from './cardapio-form';

describe('CardapioForm', () => {
  const chaveModoVisualizacaoGenero = 'sige.cardapio.seletor-genero.visualizacao';
  let component: CardapioForm;
  let fixture: ComponentFixture<CardapioForm>;
  let cardapioService: Record<string, ReturnType<typeof vi.fn>>;
  let reforcoService: Record<string, ReturnType<typeof vi.fn>>;

  const arroz: DisponibilidadeGenero = {
    item_generico_id: 1, catmat: '100001', descricao: 'Arroz', unidade_medida: 'KG', categoria: 'SM',
    categoria_descricao: 'Secos / Mercearia',
    imagem: null,
    conteudo_embalagem: null, unidade_embalagem: null, saldo_atual: 40, saldo_utilizavel: 40, reservado: 15,
    disponivel: 25, quantidade_prioritaria: 0, lotes_prioritarios: [], proxima_validade: null,
    dias_para_proxima_validade: null, status_proxima_validade: null, status_proxima_validade_descricao: null,
  };

  const sal: DisponibilidadeGenero = {
    ...arroz, item_generico_id: 2, catmat: '100002', descricao: 'Sal', saldo_atual: 0, reservado: 0, disponivel: 0,
  };

  const generoPrioritario = (
    item_generico_id: number,
    descricao: string,
    dias_para_proxima_validade: number,
  ): DisponibilidadeGenero => ({
    ...arroz,
    item_generico_id,
    descricao,
    quantidade_prioritaria: 8,
    lotes_prioritarios: [{
      id: item_generico_id,
      numero_lote: `LOTE-${item_generico_id}`,
      data_validade: '2026-11-20',
      dias_para_validade: dias_para_proxima_validade,
      status: dias_para_proxima_validade <= 7 ? 'CRITICO' : 'ATENCAO',
      status_descricao: dias_para_proxima_validade <= 7 ? 'Crítico' : 'Atenção',
      quantidade_disponivel: 8,
    }],
    proxima_validade: '2026-11-20',
    dias_para_proxima_validade,
    status_proxima_validade: dias_para_proxima_validade <= 7 ? 'CRITICO' : 'ATENCAO',
    status_proxima_validade_descricao: dias_para_proxima_validade <= 7 ? 'Crítico' : 'Atenção',
  });

  beforeEach(async () => {
    if (typeof localStorage !== 'undefined') {
      localStorage.removeItem(chaveModoVisualizacaoGenero);
    }

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
        provideRouter([]),
        { provide: ActivatedRoute, useValue: { snapshot: { queryParamMap: convertToParamMap({}) } } },
      ],
    }).compileComponents();

    vi.spyOn(TestBed.inject(Router), 'navigate').mockResolvedValue(true);

    fixture = TestBed.createComponent(CardapioForm);
    component = fixture.componentInstance;
    component.ngOnInit();

    component.refeicao = 'JANTAR';
    component.estimativaPessoas = 550;
    component.preparacoes = 'ARROZ BRANCO';
  });

  afterEach(() => {
    if (typeof localStorage !== 'undefined') {
      localStorage.removeItem(chaveModoVisualizacaoGenero);
    }
    component.ngOnDestroy();
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

  it('mostra a revisão sem salvar e mantém os dados ao voltar', () => {
    component.secoes[0].linhas[0] = { item_generico: 1, quantidade: 22, observacao: 'Cozinhar' };

    component.revisar();

    expect(component.emRevisao).toBe(true);
    expect(cardapioService['salvar']).not.toHaveBeenCalled();
    expect(component.previa?.itens[0]).toEqual(expect.objectContaining({
      descricao: 'Arroz', quantidade_planejada: 22, observacao: 'Cozinhar',
    }));
    expect(component.impactoEstoque).toEqual([
      expect.objectContaining({ quantidade: 22, restante: 3, estoqueBaixo: true }),
    ]);
    expect(component.generosComEstoqueBaixo).toBe(1);

    component.voltarParaEdicao();
    expect(component.emRevisao).toBe(false);
    expect(component.secoes[0].linhas[0].quantidade).toBe(22);
  });

  it('salva e envia ao estoque somente ao confirmar a revisão', () => {
    component.secoes[0].linhas[0] = { item_generico: 1, quantidade: 10, observacao: '' };

    component.confirmarEnvio();
    expect(cardapioService['salvar']).not.toHaveBeenCalled();

    component.revisar();
    component.confirmarEnvio();
    expect(cardapioService['salvar']).toHaveBeenCalledTimes(1);
    expect(cardapioService['enviar']).toHaveBeenCalledWith(7);
  });

  it('renderiza o painel de reforço com o empenho e permite enviar', async () => {
    const linha = { item_generico: 1, quantidade: 22, observacao: '' };
    component.secoes[0].linhas[0] = linha;
    fixture.detectChanges();

    component.abrirReforco(linha);
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    const painel: HTMLElement = fixture.nativeElement.querySelector('.reforco-painel');
    expect(painel.querySelector('.reforco-opcao')?.textContent).toContain('Empenho EMP-1');
    expect(painel.querySelector('textarea')?.value).toContain('Estoque baixo de Arroz');

    component.reforco!.quantidade = 5;
    fixture.detectChanges();
    const enviar = [...painel.querySelectorAll('button')].find((botao) => botao.textContent?.trim() === 'Enviar');
    expect(enviar?.disabled).toBe(false);
  });

  it('mostra gêneros prioritários ordenados pela validade', () => {
    const venceEmVinteDias = generoPrioritario(3, 'Feijão', 20);
    const venceEmTresDias = generoPrioritario(4, 'Macarrão', 3);
    const regular: DisponibilidadeGenero = {
      ...arroz,
      item_generico_id: 5,
      descricao: 'Óleo',
      quantidade_prioritaria: 0,
      lotes_prioritarios: [],
      proxima_validade: '2027-01-01',
      dias_para_proxima_validade: 63,
      status_proxima_validade: 'REGULAR',
      status_proxima_validade_descricao: 'Regular',
    };
    component.disponibilidade = [venceEmVinteDias, regular, venceEmTresDias];

    expect(component.generosPrioritarios.map((genero) => genero.descricao)).toEqual(['Macarrão', 'Feijão']);
  });

  it('adiciona gênero prioritário na primeira linha vazia sem preencher quantidade', () => {
    const genero = generoPrioritario(3, 'Feijão', 3);

    component.adicionarGeneroPrioritario(genero);

    expect(component.secoes[0].linhas[0]).toEqual({
      item_generico: genero.item_generico_id,
      quantidade: null,
      observacao: '',
    });
  });

  it('não adiciona novamente um gênero já presente no detalhamento', () => {
    const genero = generoPrioritario(3, 'Feijão', 3);
    component.secoes[0].linhas[0] = { item_generico: genero.item_generico_id, quantidade: null, observacao: '' };

    component.adicionarGeneroPrioritario(genero);

    const ocorrencias = component.secoes
      .flatMap((secao) => secao.linhas)
      .filter((linha) => linha.item_generico === genero.item_generico_id);
    expect(ocorrencias).toHaveLength(1);
  });

  it('apresenta o vencimento na data do cardápio sem dizer que vence hoje', () => {
    const genero: DisponibilidadeGenero = {
      ...generoPrioritario(3, 'Feijão', 0),
      lotes_prioritarios: [{
        id: 3,
        numero_lote: 'LOTE-3',
        data_validade: '2026-11-20',
        dias_para_validade: 0,
        status: 'VENCE_HOJE',
        status_descricao: 'Vence hoje',
        quantidade_disponivel: 8,
      }],
      status_proxima_validade: 'VENCE_HOJE',
      status_proxima_validade_descricao: 'Vence hoje',
    };

    expect(component.textoPrazoPrioridade(genero)).toBe('Vence na data do cardápio');
    expect(component.textoPrazoPrioridade(genero)).not.toBe('Vence hoje');
  });

  it('filtra o overlay por busca, prioridade e categoria antes de selecionar o genero', () => {
    const feijao: DisponibilidadeGenero = {
      ...generoPrioritario(3, 'Feijao', 3),
      catmat: '200003',
      categoria: 'CEREAIS',
      categoria_descricao: 'Cereais',
    };
    const linha = component.secoes[0].linhas[0];
    const overflowOriginal = document.body.style.overflow;
    component.disponibilidade = [arroz, sal, feijao];

    component.abrirSelecaoGenero(linha);

    expect(component.linhaSelecionando).toBe(linha);
    expect(document.body.style.overflow).toBe('hidden');

    component.buscaGenero = 'feijao';
    expect(component.generosParaSelecao).toEqual([feijao]);

    component.buscaGenero = '200003';
    expect(component.generosParaSelecao).toEqual([feijao]);

    component.buscaGenero = '';
    component.filtroPrioridadeGenero = 'PRIORITARIOS';
    expect(component.generosParaSelecao).toEqual([feijao]);

    component.filtroPrioridadeGenero = 'TODOS';
    component.categoriaGenero = 'CEREAIS';
    expect(component.generosParaSelecao).toEqual([feijao]);

    component.selecionarGenero(feijao);

    expect(linha.item_generico).toBe(feijao.item_generico_id);
    expect(component.linhaSelecionando).toBeNull();
    expect(document.body.style.overflow).toBe(overflowOriginal);
  });

  it('mantem a disponibilidade da data mais recente quando a consulta anterior responde depois', () => {
    const consultaAnterior = new Subject<DisponibilidadeGenero[]>();
    const consultaAtual = new Subject<DisponibilidadeGenero[]>();
    cardapioService['disponibilidade']
      .mockImplementationOnce(() => consultaAnterior)
      .mockImplementationOnce(() => consultaAtual);

    component.aoAlterarData('2026-11-10');
    component.aoAlterarData('2026-11-11');

    consultaAtual.next([sal]);
    consultaAnterior.next([arroz]);

    expect(component.data).toBe('2026-11-11');
    expect(component.disponibilidade).toEqual([sal]);
    expect(component.generoDe(sal.item_generico_id)).toEqual(sal);

    consultaAnterior.complete();
    consultaAtual.complete();
  });

  it('não exibe no seletor gêneros sem disponibilidade', () => {
    component.disponibilidade = [arroz, sal];

    expect(component.generosParaSelecao.map((genero) => genero.descricao)).toEqual(['Arroz']);
  });

  it('ordena prioritários antes dos regulares e por menor prazo', () => {
    const feijao: DisponibilidadeGenero = { ...arroz, item_generico_id: 2, descricao: 'Feijão' };
    const cenoura = generoPrioritario(3, 'Cenoura', 20);
    const alface = generoPrioritario(4, 'Alface', 3);
    component.disponibilidade = [feijao, cenoura, arroz, alface];
    component.filtroPrioridadeGenero = 'TODOS';

    expect(component.generosParaSelecao.map((genero) => genero.descricao)).toEqual([
      'Alface', 'Cenoura', 'Arroz', 'Feijão',
    ]);
  });

  it('ordena os prioritários por menor prazo de validade', () => {
    const venceEmQuinzeDias = generoPrioritario(2, 'A', 15);
    const venceEmDoisDias = generoPrioritario(3, 'B', 2);
    const venceEmSeteDias = generoPrioritario(4, 'C', 7);
    component.disponibilidade = [venceEmQuinzeDias, venceEmDoisDias, venceEmSeteDias];
    component.filtroPrioridadeGenero = 'PRIORITARIOS';

    expect(component.generosParaSelecao.map((genero) => genero.descricao)).toEqual(['B', 'C', 'A']);
  });

  it('identifica o gênero atualmente selecionado no overlay', () => {
    const linha = component.secoes[0].linhas[0];
    linha.item_generico = 123;
    component.linhaSelecionando = linha;

    expect(component.generoSelecionadoNoOverlay({ ...arroz, item_generico_id: 123 })).toBe(true);
    expect(component.generoSelecionadoNoOverlay({ ...arroz, item_generico_id: 456 })).toBe(false);
  });

  it('deriva categorias exibíveis com descrições amigáveis', () => {
    const frutas: DisponibilidadeGenero = {
      ...arroz,
      item_generico_id: 3,
      categoria: 'Fr',
      categoria_descricao: 'Frutas',
    };
    const proteinas: DisponibilidadeGenero = {
      ...arroz,
      item_generico_id: 4,
      categoria: 'Pr',
      categoria_descricao: 'Proteínas',
    };
    component.disponibilidade = [proteinas, frutas];

    expect(component.categoriasGeneros).toEqual([
      { valor: 'Fr', descricao: 'Frutas' },
      { valor: 'Pr', descricao: 'Proteínas' },
    ]);
  });

  it('apresenta a descrição amigável da categoria no seletor', () => {
    const frutas: DisponibilidadeGenero = {
      ...arroz,
      item_generico_id: 3,
      categoria: 'Fr',
      categoria_descricao: 'Frutas',
    };
    const lacteos: DisponibilidadeGenero = {
      ...arroz,
      item_generico_id: 4,
      categoria: 'Lac',
      categoria_descricao: 'Lácteos e Derivados',
    };
    component.disponibilidade = [frutas, lacteos];
    component.abrirSelecaoGenero(component.secoes[0].linhas[0]);
    fixture.detectChanges();

    const seletor: HTMLSelectElement | null = fixture.nativeElement.querySelector('#categoria-genero');
    expect(seletor).not.toBeNull();
    const opcoes = Array.from(seletor!.options).map((opcao) => opcao.textContent?.trim());
    expect(opcoes).toContain('Frutas');
    expect(opcoes).toContain('Lácteos e Derivados');
    expect(opcoes).not.toContain('Fr');
    expect(opcoes).not.toContain('Lac');
    expect(opcoes).not.toContain('SM');

    component.fecharSelecaoGenero();
  });

  it('alterna entre os modos de cards e tabela', () => {
    expect(component.modoVisualizacaoGenero).toBe('cards');

    component.alterarModoVisualizacaoGenero('tabela');
    expect(component.modoVisualizacaoGenero).toBe('tabela');

    component.alterarModoVisualizacaoGenero('cards');
    expect(component.modoVisualizacaoGenero).toBe('cards');
  });

  it('persiste localmente o modo de visualização escolhido', () => {
    component.alterarModoVisualizacaoGenero('tabela');

    expect(localStorage.getItem(chaveModoVisualizacaoGenero)).toBe('tabela');
  });

  it('conta os resultados filtrados e limpa somente os filtros', () => {
    component.alterarModoVisualizacaoGenero('tabela');
    component.buscaGenero = 'inexistente';
    component.categoriaGenero = 'SM';
    component.filtroPrioridadeGenero = 'PRIORITARIOS';

    expect(component.quantidadeResultadosGenero).toBe(component.generosParaSelecao.length);
    expect(component.quantidadeResultadosGenero).toBe(0);
    expect(component.temFiltrosGeneroAtivos).toBe(true);

    component.limparFiltrosGenero();

    expect(component.buscaGenero).toBe('');
    expect(component.categoriaGenero).toBe('');
    expect(component.filtroPrioridadeGenero).toBe('TODOS');
    expect(component.modoVisualizacaoGenero).toBe('tabela');
    expect(component.quantidadeResultadosGenero).toBe(component.generosParaSelecao.length);
  });

  it('mostra a data civil concreta no cabeçalho do seletor', () => {
    component.data = '2026-11-20';
    component.abrirSelecaoGenero(component.secoes[0].linhas[0]);
    fixture.detectChanges();

    const seletor: HTMLElement | null = fixture.nativeElement.querySelector('.seletor-genero');
    expect(seletor?.textContent).toContain('20/11/2026');

    component.fecharSelecaoGenero();
  });

  it('permite exibir foto real para gênero com imagem', () => {
    const generoComImagem: DisponibilidadeGenero = {
      ...arroz,
      imagem: '/media/generos/alface.jpg',
    };

    expect(component.podeExibirImagemGenero(generoComImagem)).toBe(true);
  });

  it('usa o ícone de categoria quando o gênero não possui imagem', () => {
    expect(component.urlImagemGenero(arroz)).toBeNull();
    expect(component.podeExibirImagemGenero(arroz)).toBe(false);
  });

  it('resolve a imagem relativa com a origem da API quando ela é absoluta', () => {
    const generoComImagem: DisponibilidadeGenero = {
      ...arroz,
      imagem: '/media/generos/alface.jpg',
    };
    const caminho = '/media/generos/alface.jpg';
    const esperado = /^https?:\/\//i.test(environment.API_URL)
      ? `${new URL(environment.API_URL).origin}${caminho}`
      : caminho;

    expect(component.urlImagemGenero(generoComImagem)).toBe(esperado);
  });

  it('preserva URL absoluta da imagem', () => {
    const imagem = 'https://cdn.exemplo.com/alface.jpg';
    const generoComImagem: DisponibilidadeGenero = { ...arroz, imagem };

    expect(component.urlImagemGenero(generoComImagem)).toBe(imagem);
  });

  it('normaliza imagem relativa sem barra inicial', () => {
    const generoComImagem: DisponibilidadeGenero = {
      ...arroz,
      imagem: 'media/generos/alface.jpg',
    };
    const caminho = '/media/generos/alface.jpg';
    const esperado = /^https?:\/\//i.test(environment.API_URL)
      ? `${new URL(environment.API_URL).origin}${caminho}`
      : caminho;

    expect(component.urlImagemGenero(generoComImagem)).toBe(esperado);
  });

  it('usa o ícone de categoria após falha no carregamento da imagem', () => {
    const generoComImagem: DisponibilidadeGenero = {
      ...arroz,
      imagem: '/media/generos/alface.jpg',
    };

    component.aoErroImagemGenero(generoComImagem.item_generico_id);

    expect(component.podeExibirImagemGenero(generoComImagem)).toBe(false);
  });
});
