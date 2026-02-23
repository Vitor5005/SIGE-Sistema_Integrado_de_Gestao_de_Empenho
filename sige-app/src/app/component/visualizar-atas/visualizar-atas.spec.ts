import { ComponentFixture, TestBed } from '@angular/core/testing';

import { VisualizarAtas } from './visualizar-atas';

describe('VisualizarAtas', () => {
  let component: VisualizarAtas;
  let fixture: ComponentFixture<VisualizarAtas>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [VisualizarAtas]
    })
    .compileComponents();

    fixture = TestBed.createComponent(VisualizarAtas);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
