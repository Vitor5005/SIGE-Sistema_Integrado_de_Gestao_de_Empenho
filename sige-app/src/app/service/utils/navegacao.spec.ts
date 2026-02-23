import { TestBed } from '@angular/core/testing';

import { Navegacao } from './navegacao';

describe('Navegacao', () => {
  let service: Navegacao;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(Navegacao);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
