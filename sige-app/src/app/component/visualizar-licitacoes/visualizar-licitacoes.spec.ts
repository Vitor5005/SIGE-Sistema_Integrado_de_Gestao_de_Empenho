import { ComponentFixture, TestBed } from '@angular/core/testing';

import { VisualizarLicitacoes } from './visualizar-licitacoes';

describe('VisualizarLicitacoes', () => {
  let component: VisualizarLicitacoes;
  let fixture: ComponentFixture<VisualizarLicitacoes>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [VisualizarLicitacoes]
    })
    .compileComponents();

    fixture = TestBed.createComponent(VisualizarLicitacoes);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
