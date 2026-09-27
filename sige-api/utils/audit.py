from datetime import date, datetime
from decimal import Decimal

from django.forms.models import model_to_dict

from utils.rbac import resolver_acao


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


class AuditoriaRBACMixin:
    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        self._auditoria_anterior = {}
        self._auditoria_instancia_id = kwargs.get(
            getattr(self, 'lookup_url_kwarg', None) or getattr(self, 'lookup_field', 'pk')
        )

        if request.method in {'PUT', 'PATCH', 'DELETE', 'POST'} and self._auditoria_instancia_id:
            queryset = self.get_queryset()
            instancia = queryset.model._default_manager.filter(
                pk=self._auditoria_instancia_id
            ).first()
            self._auditoria_anterior = serializar_instancia(instancia)

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)

        acao = getattr(request, '_rbac_acao', None)
        recurso = getattr(request, '_rbac_recurso', None)
        if (
            request.method not in {'POST', 'PUT', 'PATCH', 'DELETE'}
            or response.status_code >= 400
            or not acao
            or not recurso
        ):
            return response

        queryset = self.get_queryset()
        model = queryset.model
        entidade_id = self._auditoria_instancia_id
        if entidade_id is None and isinstance(getattr(response, 'data', None), dict):
            entidade_id = response.data.get('id')

        instancia_nova = None
        if request.method != 'DELETE' and entidade_id is not None:
            instancia_nova = model._default_manager.filter(pk=entidade_id).first()

        registrar_auditoria(
            usuario=request.user,
            papel=getattr(request.user, 'papel', ''),
            acao=acao,
            recurso=recurso,
            entidade=model._meta.label,
            entidade_id=entidade_id,
            valores_anteriores=getattr(self, '_auditoria_anterior', {}),
            valores_novos=(
                serializar_instancia(instancia_nova)
                if instancia_nova is not None
                else serializar_dados(getattr(request, 'data', {}))
            ),
            permitido=True,
        )
        return response
