import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { of } from 'rxjs';
import { vi } from 'vitest';

import { AdicionarLicitacao } from './adicionar-licitacao';
import { LicitacaoService } from '../../service/licitacao.service';

describe('AdicionarLicitacao', () => {
  let component: AdicionarLicitacao;
  let fixture: ComponentFixture<AdicionarLicitacao>;
  let licitacaoService: { getAtual: ReturnType<typeof vi.fn>; save: ReturnType<typeof vi.fn> };

  beforeEach(async () => {
    licitacaoService = {
      getAtual: vi.fn(() => of(null)),
      save: vi.fn(() => of({ id: 1 })),
    };

    await TestBed.configureTestingModule({
      imports: [AdicionarLicitacao],
      providers: [
        { provide: LicitacaoService, useValue: licitacaoService },
        { provide: Router, useValue: { navigate: vi.fn() } },
      ],
    })
    .compileComponents();

    fixture = TestBed.createComponent(AdicionarLicitacao);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  function preencherFormulario(): void {
    component.licitacao.numero_licitacao = ' 001/2026 ';
    component.licitacao.validade = '12';
    component.licitacao.data_abertura = component.todayDate;
    component.licitacao.descricao = 'Gêneros alimentícios';
  }

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('exibe a revisão sem criar a licitação', () => {
    preencherFormulario();

    component.revisar();

    expect(component.emRevisao).toBe(true);
    expect(component.licitacao.numero_licitacao).toBe('001/2026');
    expect(licitacaoService.save).not.toHaveBeenCalled();
  });

  it('mantém os dados ao voltar para a edição', () => {
    preencherFormulario();
    component.revisar();

    component.voltarParaEdicao();

    expect(component.emRevisao).toBe(false);
    expect(component.licitacao.numero_licitacao).toBe('001/2026');
    expect(component.licitacao.descricao).toBe('Gêneros alimentícios');
    expect(licitacaoService.save).not.toHaveBeenCalled();
  });

  it('cria a licitação somente após a confirmação', () => {
    preencherFormulario();

    component.save();
    expect(licitacaoService.save).not.toHaveBeenCalled();

    component.revisar();
    component.save();
    expect(licitacaoService.save).toHaveBeenCalledTimes(1);
  });

  it('não exibe erro de data enquanto a data informada é válida', () => {
    component.licitacao.data_abertura = component.todayDate;
    expect(component.exibirErroDataAbertura(true)).toBe(false);

    component.licitacao.data_abertura = '2999-01-01';
    expect(component.exibirErroDataAbertura(false)).toBe(false);
    expect(component.exibirErroDataAbertura(true)).toBe(true);
  });
});
