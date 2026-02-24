import { ComponentFixture, TestBed } from '@angular/core/testing';

import { VisualizarFornecedores } from './visualizar-fornecedores';

describe('VisualizarFornecedores', () => {
  let component: VisualizarFornecedores;
  let fixture: ComponentFixture<VisualizarFornecedores>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [VisualizarFornecedores]
    })
    .compileComponents();

    fixture = TestBed.createComponent(VisualizarFornecedores);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
