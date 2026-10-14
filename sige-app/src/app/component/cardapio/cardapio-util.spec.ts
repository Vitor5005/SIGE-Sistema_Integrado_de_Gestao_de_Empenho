import { nomeArquivoCardapio } from './cardapio-util';

describe('nomeArquivoCardapio', () => {
  it('usa a refeição e a data no padrão dia-mês-ano', () => {
    expect(nomeArquivoCardapio({ refeicao: 'JANTAR', data: '2026-10-14' })).toBe('jantar-14-10-2026');
    expect(nomeArquivoCardapio({ refeicao: 'ALMOCO', data: '2025-09-29' })).toBe('almoço-29-09-2025');
    expect(nomeArquivoCardapio({ refeicao: 'CAFE', data: '2026-01-05' })).toBe('cafe-05-01-2026');
  });
});
