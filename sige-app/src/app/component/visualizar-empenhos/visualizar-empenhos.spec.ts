import { ComponentFixture, TestBed } from '@angular/core/testing';

import { VisualizarEmpenhos } from './visualizar-empenhos';

describe('VisualizarEmpenhos', () => {
  let component: VisualizarEmpenhos;
  let fixture: ComponentFixture<VisualizarEmpenhos>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [VisualizarEmpenhos]
    })
    .compileComponents();

    fixture = TestBed.createComponent(VisualizarEmpenhos);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
