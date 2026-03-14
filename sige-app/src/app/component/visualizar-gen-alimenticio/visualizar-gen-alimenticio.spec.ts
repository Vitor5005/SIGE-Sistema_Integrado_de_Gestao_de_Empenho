import { ComponentFixture, TestBed } from '@angular/core/testing';

import { VisualizarGenAlimenticio } from './visualizar-gen-alimenticio';

describe('VisualizarGenAlimenticio', () => {
  let component: VisualizarGenAlimenticio;
  let fixture: ComponentFixture<VisualizarGenAlimenticio>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [VisualizarGenAlimenticio]
    })
    .compileComponents();

    fixture = TestBed.createComponent(VisualizarGenAlimenticio);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
