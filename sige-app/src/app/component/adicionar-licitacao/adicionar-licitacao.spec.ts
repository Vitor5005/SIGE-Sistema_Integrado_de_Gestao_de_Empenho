import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AdicionarLicitacao } from './adicionar-licitacao';

describe('AdicionarLicitacao', () => {
  let component: AdicionarLicitacao;
  let fixture: ComponentFixture<AdicionarLicitacao>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AdicionarLicitacao]
    })
    .compileComponents();

    fixture = TestBed.createComponent(AdicionarLicitacao);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
