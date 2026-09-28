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

  it('permite a Diretor, Técnico e Estoquista cadastrar gêneros alimentícios', () => {
    expect(temPermissao(Papel.DIRETOR, Recurso.GENERO_ALIMENTICIO, Acao.CADASTRAR)).toBe(true);
    expect(temPermissao(Papel.TECNICO_ADMINISTRATIVO, Recurso.GENERO_ALIMENTICIO, Acao.CADASTRAR)).toBe(true);
    expect(temPermissao(Papel.ESTOQUISTA, Recurso.GENERO_ALIMENTICIO, Acao.CADASTRAR)).toBe(true);
    expect(temPermissao(Papel.NUTRICIONISTA, Recurso.GENERO_ALIMENTICIO, Acao.CADASTRAR)).toBe(false);
  });

  it('permite somente ao Diretor excluir fornecedores e gêneros alimentícios', () => {
    expect(temPermissao(Papel.DIRETOR, Recurso.FORNECEDOR, Acao.EXCLUIR)).toBe(true);
    expect(temPermissao(Papel.TECNICO_ADMINISTRATIVO, Recurso.FORNECEDOR, Acao.EXCLUIR)).toBe(false);
    expect(temPermissao(Papel.NUTRICIONISTA, Recurso.FORNECEDOR, Acao.EXCLUIR)).toBe(false);
    expect(temPermissao(Papel.ESTOQUISTA, Recurso.FORNECEDOR, Acao.EXCLUIR)).toBe(false);

    expect(temPermissao(Papel.DIRETOR, Recurso.GENERO_ALIMENTICIO, Acao.EXCLUIR)).toBe(true);
    expect(temPermissao(Papel.TECNICO_ADMINISTRATIVO, Recurso.GENERO_ALIMENTICIO, Acao.EXCLUIR)).toBe(false);
    expect(temPermissao(Papel.NUTRICIONISTA, Recurso.GENERO_ALIMENTICIO, Acao.EXCLUIR)).toBe(false);
    expect(temPermissao(Papel.ESTOQUISTA, Recurso.GENERO_ALIMENTICIO, Acao.EXCLUIR)).toBe(false);
  });

  it('não dá ao Estoquista acesso a licitações, ARPs e empenhos', () => {
    expect(temPermissao(Papel.ESTOQUISTA, Recurso.LICITACAO, Acao.CONSULTAR)).toBe(false);
    expect(temPermissao(Papel.ESTOQUISTA, Recurso.ATA, Acao.CONSULTAR)).toBe(false);
    expect(temPermissao(Papel.ESTOQUISTA, Recurso.EMPENHO, Acao.CONSULTAR)).toBe(false);
  });

  it('alerta somente Diretor e Técnico sobre pendências de fornecedores', () => {
    expect(temPermissao(Papel.DIRETOR, Recurso.PENDENCIA_FORNECEDOR, Acao.ALTERAR_STATUS)).toBe(true);
    expect(temPermissao(Papel.TECNICO_ADMINISTRATIVO, Recurso.PENDENCIA_FORNECEDOR, Acao.ALTERAR_STATUS)).toBe(true);
    expect(temPermissao(Papel.ESTOQUISTA, Recurso.PENDENCIA_FORNECEDOR, Acao.ALTERAR_STATUS)).toBe(false);
    expect(temPermissao(Papel.NUTRICIONISTA, Recurso.PENDENCIA_FORNECEDOR, Acao.ALTERAR_STATUS)).toBe(false);
  });

  it('aplica as permissões de consulta do estoque', () => {
    expect(temPermissao(Papel.NUTRICIONISTA, Recurso.MOVIMENTACAO_ESTOQUE, Acao.CONSULTAR_EXTRATO)).toBe(true);
    expect(temPermissao(Papel.TECNICO_ADMINISTRATIVO, Recurso.MOVIMENTACAO_ESTOQUE, Acao.CONSULTAR_EXTRATO)).toBe(false);
    expect(temPermissao(Papel.TECNICO_ADMINISTRATIVO, Recurso.ESTOQUE, Acao.CONSULTAR_CONSOLIDADO)).toBe(true);
  });

  it('permite somente ao Diretor excluir licitações e ARPs', () => {
    expect(temPermissao(Papel.DIRETOR, Recurso.LICITACAO, Acao.EXCLUIR)).toBe(true);
    expect(temPermissao(Papel.TECNICO_ADMINISTRATIVO, Recurso.LICITACAO, Acao.EXCLUIR)).toBe(false);
    expect(temPermissao(Papel.NUTRICIONISTA, Recurso.LICITACAO, Acao.EXCLUIR)).toBe(false);
    expect(temPermissao(Papel.ESTOQUISTA, Recurso.LICITACAO, Acao.EXCLUIR)).toBe(false);

    expect(temPermissao(Papel.DIRETOR, Recurso.ATA, Acao.EXCLUIR)).toBe(true);
    expect(temPermissao(Papel.TECNICO_ADMINISTRATIVO, Recurso.ATA, Acao.EXCLUIR)).toBe(false);
    expect(temPermissao(Papel.NUTRICIONISTA, Recurso.ATA, Acao.EXCLUIR)).toBe(false);
    expect(temPermissao(Papel.ESTOQUISTA, Recurso.ATA, Acao.EXCLUIR)).toBe(false);
  });

  it('mantém solicitação de reforço separada da operação financeira', () => {
    expect(temPermissao(Papel.NUTRICIONISTA, Recurso.SOLICITACAO_REFORCO, Acao.SOLICITAR_REFORCO)).toBe(true);
    expect(temPermissao(Papel.DIRETOR, Recurso.SOLICITACAO_REFORCO, Acao.SOLICITAR_REFORCO)).toBe(false);
    expect(temPermissao(Papel.DIRETOR, Recurso.SOLICITACAO_REFORCO, Acao.ALTERAR_STATUS)).toBe(true);
    expect(temPermissao(Papel.NUTRICIONISTA, Recurso.SOLICITACAO_REFORCO, Acao.ALTERAR_STATUS)).toBe(false);
    expect(temPermissao(Papel.DIRETOR, Recurso.OPERACAO_EMPENHO, Acao.REFORCAR_EMPENHO)).toBe(true);
    expect(temPermissao(Papel.NUTRICIONISTA, Recurso.OPERACAO_EMPENHO, Acao.REFORCAR_EMPENHO)).toBe(false);
  });
});

