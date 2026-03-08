from rest_framework.routers import DefaultRouter
from .views import (
    EmpenhoViewSet,
    ItemEmpenhoViewSet,
    OperacaoItemViewSet,
    ItemDoEmpehoViewSet,
    OperacaoDoEmpenhoViewSet
)

router = DefaultRouter()

router.register(r'empenhos/operacaoDoEmpenho', OperacaoDoEmpenhoViewSet, basename='operacoes-do-empenho')
router.register(r'empenhos/itensDoEmpenho', ItemDoEmpehoViewSet, basename='itens-do-empenho')
router.register(r'empenhos',EmpenhoViewSet)
router.register(r'itemempenho', ItemEmpenhoViewSet)
router.register(r'operacaoitens', OperacaoItemViewSet)

urlpatterns = router.urls