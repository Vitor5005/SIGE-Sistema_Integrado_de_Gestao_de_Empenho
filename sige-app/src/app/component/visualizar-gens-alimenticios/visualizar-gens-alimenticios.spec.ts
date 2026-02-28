import { ComponentFixture, TestBed } from '@angular/core/testing';

import { VisualizarGensAlimenticios } from './visualizar-gens-alimenticios';

describe('VisualizarGensAlimenticios', () => {
  let component: VisualizarGensAlimenticios;
  let fixture: ComponentFixture<VisualizarGensAlimenticios>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [VisualizarGensAlimenticios]
    })
    .compileComponents();

    fixture = TestBed.createComponent(VisualizarGensAlimenticios);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
