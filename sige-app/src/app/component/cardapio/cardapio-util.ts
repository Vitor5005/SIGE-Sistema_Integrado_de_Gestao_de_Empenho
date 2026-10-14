import { RefeicaoCardapio, StatusCardapio } from '../../model/cardapio';

/** Classe do selo de situação do cardápio, compartilhada entre listagem, detalhe e notificações. */
export function classeStatusCardapio(status: StatusCardapio): string {
  const classes: Record<StatusCardapio, string> = {
    RASCUNHO: 'status-cardapio--rascunho',
    ENVIADO: 'status-cardapio--aguardando',
    RECUSADO: 'status-cardapio--recusado',
    APROVADO: 'status-cardapio--aprovado',
    CONSUMO_INFORMADO: 'status-cardapio--aguardando',
    FINALIZADO: 'status-cardapio--finalizado',
  };
  return `status-cardapio ${classes[status] ?? ''}`;
}

/** Ex.: "GAR (900 mL)" para um gênero vendido em garrafas de 900 mL. */
export function unidadeComEmbalagem(item: {
  unidade_medida?: string;
  conteudo_embalagem?: number | string | null;
  unidade_embalagem?: string | null;
}): string {
  const unidade = item.unidade_medida || '';
  if (!item.conteudo_embalagem) {
    return unidade;
  }
  const conteudo = Number(item.conteudo_embalagem).toLocaleString('pt-BR', { maximumFractionDigits: 3 });
  return `${unidade} (${conteudo} ${item.unidade_embalagem || ''})`.trim();
}

/** Quantidade com até 3 casas decimais no padrão brasileiro. */
export function formatarQuantidade(valor: number | string | null | undefined): string {
  if (valor === null || valor === undefined || valor === '') {
    return '—';
  }
  return Number(valor).toLocaleString('pt-BR', { maximumFractionDigits: 3 });
}

/** Agrupa os itens do cardápio pela seção do detalhamento, preservando a ordem. */
export function agruparPorSecao<T extends { secao: string }>(itens: T[]): { secao: string; itens: T[] }[] {
  const grupos: { secao: string; itens: T[] }[] = [];
  for (const item of itens) {
    let grupo = grupos.find((g) => g.secao === item.secao);
    if (!grupo) {
      grupo = { secao: item.secao, itens: [] };
      grupos.push(grupo);
    }
    grupo.itens.push(item);
  }
  return grupos;
}

const NOME_REFEICAO_ARQUIVO: Record<RefeicaoCardapio, string> = {
  CAFE: 'cafe',
  ALMOCO: 'almoço',
  JANTAR: 'jantar',
};

/** Nome do arquivo do documento: refeição e data, ex.: "jantar-14-10-2026". */
export function nomeArquivoCardapio(cardapio: { refeicao: RefeicaoCardapio; data: string }): string {
  const [ano, mes, dia] = cardapio.data.split('-');
  return `${NOME_REFEICAO_ARQUIVO[cardapio.refeicao] ?? cardapio.refeicao.toLowerCase()}-${dia}-${mes}-${ano}`;
}
