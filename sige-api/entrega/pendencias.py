from decimal import Decimal

from django.utils import timezone

from entrega.models import PendenciaFornecedor
from utils.rbac import Acao


ZERO = Decimal('0.000')
MOTIVO_ITEM_NAO_ENTREGUE = 'Item não entregue neste recebimento.'


def resolver_solicitante(ordem):
    """Usuário que gerou a ordem; para ordens antigas, busca no histórico de auditoria."""
    if ordem.solicitante_id:
        return ordem.solicitante

    from usuario.models import HistoricoAuditoria

    evento = (
        HistoricoAuditoria.objects
        .filter(
            entidade='entrega.OrdemEntrega',
            entidade_id=str(ordem.pk),
            acao=Acao.GERAR_ORDEM,
            permitido=True,
            usuario__isnull=False,
        )
        .select_related('usuario')
        .order_by('data_hora', 'id')
        .first()
    )
    return evento.usuario if evento else None


def sincronizar_pendencias(*, ordem, itens_ordem, recebidos_por_id, usuario):
    """
    Após um recebimento, registra (ou atualiza) a pendência de cada item que
    continua com saldo a entregar e resolve as que foram quitadas.
    """
    agora = timezone.now()
    abertas = {
        pendencia.item_ordem_id: pendencia
        for pendencia in PendenciaFornecedor.objects.select_for_update().filter(
            item_ordem__ordem_entrega=ordem,
        ).exclude(status=PendenciaFornecedor.Status.RESOLVIDA)
    }
    destinatario = None
    destinatario_resolvido = False
    pendencias = []

    for item in itens_ordem:
        pendente = (Decimal(item.quantidade_solicitada) - Decimal(item.quantidade_entregue)).quantize(ZERO)
        aberta = abertas.get(item.pk)

        if pendente <= ZERO:
            if aberta:
                aberta.status = PendenciaFornecedor.Status.RESOLVIDA
                aberta.quantidade_pendente = ZERO
                aberta.data_resolucao = agora
                aberta.save(update_fields=['status', 'quantidade_pendente', 'data_resolucao', 'data_atualizacao'])
            continue

        recebido = recebidos_por_id.get(item.pk)
        if recebido is None and aberta:
            # Item não tratado neste recebimento: a pendência existente permanece como está.
            continue

        motivo = str((recebido or {}).get('observacao') or '').strip() or MOTIVO_ITEM_NAO_ENTREGUE

        if not destinatario_resolvido:
            destinatario = resolver_solicitante(ordem)
            destinatario_resolvido = True

        if aberta:
            aberta.quantidade_pendente = pendente
            aberta.motivo = motivo
            aberta.registrada_por = usuario
            # Nova entrega incompleta: volta a alertar quem já havia dado ciência.
            aberta.status = PendenciaFornecedor.Status.ABERTA
            aberta.ciente_por = None
            aberta.data_ciencia = None
            aberta.save()
            pendencias.append(aberta)
        else:
            pendencias.append(PendenciaFornecedor.objects.create(
                item_ordem=item,
                quantidade_pendente=pendente,
                motivo=motivo,
                registrada_por=usuario,
                destinatario=destinatario,
            ))

    return pendencias
