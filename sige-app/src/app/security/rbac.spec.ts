import { Acao, Papel, Recurso, temPermissao } from './rbac';

describe('matriz RBAC', () => {
  it('permite somente ao Diretor gerenciar usuários', () => {
    expect(temPermissao(Papel.DIRETOR, Recurso.USUARIO, Acao.CADASTRAR)).toBe(true);
    expect(temPermissao(Papel.TECNICO_ADMINISTRATIVO, Recurso.USUARIO, Acao.CADASTRAR)).toBe(false);
    expect(temPermissao(Papel.NUTRICIONISTA, Recurso.USUARIO, Acao.CADASTRAR)).toBe(false);
    expect(temPermissao(Papel.ESTOQUISTA, Recurso.USUARIO, Acao.CADASTRAR)).toBe(false);
  });

  it('permite somente ao Técnico Administrativo gerar ordens', () => {
    expect(temPermissao(Papel.DIRETOR, Recurso.ORDEM_ENTREGA, Acao.GERAR_ORDEM)).toBe(false);
    expect(temPermissao(Papel.TECNICO_ADMINISTRATIVO, Recurso.ORDEM_ENTREGA, Acao.GERAR_ORDEM)).toBe(true);
    expect(temPermissao(Papel.NUTRICIONISTA, Recurso.ORDEM_ENTREGA, Acao.GERAR_ORDEM)).toBe(false);
    expect(temPermissao(Papel.ESTOQUISTA, Recurso.ORDEM_ENTREGA, Acao.GERAR_ORDEM)).toBe(false);
  });

  it('permite somente ao Estoquista registrar recebimento', () => {
    expect(temPermissao(Papel.DIRETOR, Recurso.ESTOQUE, Acao.REGISTRAR_RECEBIMENTO)).toBe(false);
    expect(temPermissao(Papel.TECNICO_ADMINISTRATIVO, Recurso.ESTOQUE, Acao.REGISTRAR_RECEBIMENTO)).toBe(false);
    expect(temPermissao(Papel.NUTRICIONISTA, Recurso.ESTOQUE, Acao.REGISTRAR_RECEBIMENTO)).toBe(false);
    expect(temPermissao(Papel.ESTOQUISTA, Recurso.ESTOQUE, Acao.REGISTRAR_RECEBIMENTO)).toBe(true);
  });

  it('aplica as permissões de consulta do estoque', () => {
    expect(temPermissao(Papel.NUTRICIONISTA, Recurso.MOVIMENTACAO_ESTOQUE, Acao.CONSULTAR_EXTRATO)).toBe(true);
    expect(temPermissao(Papel.TECNICO_ADMINISTRATIVO, Recurso.MOVIMENTACAO_ESTOQUE, Acao.CONSULTAR_EXTRATO)).toBe(false);
    expect(temPermissao(Papel.TECNICO_ADMINISTRATIVO, Recurso.ESTOQUE, Acao.CONSULTAR_CONSOLIDADO)).toBe(true);
  });
});

