import { ComponentFixture, TestBed } from '@angular/core/testing';

import { VisualizarEntregas } from './visualizar-entregas';

describe('VisualizarEntregas', () => {
  let component: VisualizarEntregas;
  let fixture: ComponentFixture<VisualizarEntregas>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [VisualizarEntregas]
    })
    .compileComponents();

    fixture = TestBed.createComponent(VisualizarEntregas);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
