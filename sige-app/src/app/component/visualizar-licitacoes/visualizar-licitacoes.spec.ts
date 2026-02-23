import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Licitacoes } from './visualizar-licitacoes';

describe('Licitacoes', () => {
  let component: Licitacoes;
  let fixture: ComponentFixture<Licitacoes>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Licitacoes]
    })
    .compileComponents();

    fixture = TestBed.createComponent(Licitacoes);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
