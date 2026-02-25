import { ComponentFixture, TestBed } from '@angular/core/testing';

import { VisualizarFornecedor } from './visualizar-fornecedor';

describe('VisualizarFornecedor', () => {
  let component: VisualizarFornecedor;
  let fixture: ComponentFixture<VisualizarFornecedor>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [VisualizarFornecedor]
    })
    .compileComponents();

    fixture = TestBed.createComponent(VisualizarFornecedor);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
