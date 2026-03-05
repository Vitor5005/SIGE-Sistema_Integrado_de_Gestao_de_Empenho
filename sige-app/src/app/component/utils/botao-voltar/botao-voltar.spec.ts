import { ComponentFixture, TestBed } from '@angular/core/testing';

import { BotaoVoltar } from './botao-voltar';

describe('BotaoVoltar', () => {
  let component: BotaoVoltar;
  let fixture: ComponentFixture<BotaoVoltar>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [BotaoVoltar]
    })
    .compileComponents();

    fixture = TestBed.createComponent(BotaoVoltar);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
