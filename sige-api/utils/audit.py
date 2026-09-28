from datetime import date, datetime
from decimal import Decimal

from django.forms.models import model_to_dict


CAMPOS_SENSIVEIS = {'password', 'senha', 'token', 'access', 'refresh', 'reset_token'}


def _valor_json(valor):
    if isinstance(valor, dict):
        return {
            chave: '***' if chave.lower() in CAMPOS_SENSIVEIS else _valor_json(item)
            for chave, item in valor.items()
        }
    if isinstance(valor, (list, tuple)):
        return [_valor_json(item) for item in valor]
    if isinstance(valor, (date, datetime, Decimal)):
        return str(valor)
    if hasattr(valor, 'name') and hasattr(valor, 'size'):
        return {'arquivo': valor.name, 'tamanho': valor.size}
    if isinstance(valor, (str, int, float, bool)) or valor is None:
        return valor
    return str(valor)


def serializar_dados(dados):
    if dados is None:
        return {}
    if hasattr(dados, 'dict'):
        dados = dados.dict()
    return _valor_json(dict(dados))


def serializar_instancia(instancia):
    if instancia is None:
        return {}
    dados = model_to_dict(instancia)
    dados['id'] = instancia.pk
    return serializar_dados(dados)


def registrar_auditoria(
    *, usuario, papel, acao, recurso, entidade='', entidade_id=None,
    valores_anteriores=None, valores_novos=None, permitido=True, detalhe=''
):
    from usuario.models import HistoricoAuditoria

    return HistoricoAuditoria.objects.create(
        usuario=usuario if getattr(usuario, 'is_authenticated', False) else None,
        papel=papel or '',
        acao=acao or '',
        recurso=recurso or '',
        entidade=entidade or '',
        entidade_id=str(entidade_id) if entidade_id is not None else None,
        valores_anteriores=serializar_dados(valores_anteriores),
        valores_novos=serializar_dados(valores_novos),
        permitido=permitido,
        detalhe=detalhe,
    )

