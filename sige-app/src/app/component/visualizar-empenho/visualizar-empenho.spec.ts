import { ComponentFixture, TestBed } from '@angular/core/testing';

import { VisualizarEmpenho } from './visualizar-empenho';

describe('VisualizarEmpenho', () => {
  let component: VisualizarEmpenho;
  let fixture: ComponentFixture<VisualizarEmpenho>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [VisualizarEmpenho]
    })
    .compileComponents();

    fixture = TestBed.createComponent(VisualizarEmpenho);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
