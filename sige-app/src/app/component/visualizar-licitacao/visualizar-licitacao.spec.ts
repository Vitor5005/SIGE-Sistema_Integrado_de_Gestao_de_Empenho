import { ComponentFixture, TestBed } from '@angular/core/testing';

import { VisualizarLicitacao } from './visualizar-licitacao';

describe('VisualizarLicitacao', () => {
  let component: VisualizarLicitacao;
  let fixture: ComponentFixture<VisualizarLicitacao>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [VisualizarLicitacao]
    })
    .compileComponents();

    fixture = TestBed.createComponent(VisualizarLicitacao);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
