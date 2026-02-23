import { ComponentFixture, TestBed } from '@angular/core/testing';

import { VisualizarAta } from './visualizar-ata';

describe('VisualizarAta', () => {
  let component: VisualizarAta;
  let fixture: ComponentFixture<VisualizarAta>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [VisualizarAta]
    })
    .compileComponents();

    fixture = TestBed.createComponent(VisualizarAta);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
