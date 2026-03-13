import { ComponentFixture, TestBed } from '@angular/core/testing';

import { VisualizarUsuarios } from './visualizar-usuarios';

describe('VisualizarUsuarios', () => {
  let component: VisualizarUsuarios;
  let fixture: ComponentFixture<VisualizarUsuarios>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [VisualizarUsuarios]
    })
    .compileComponents();

    fixture = TestBed.createComponent(VisualizarUsuarios);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
