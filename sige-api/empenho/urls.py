from rest_framework.routers import DefaultRouter
from .views import (
    EmpenhoViewSet,
    ItemEmpenhoViewSet,
    OperacaoItemViewSet
)

router = DefaultRouter()

router.register(r'empenhos',EmpenhoViewSet)
router.register(r'itemempenho', ItemEmpenhoViewSet)
router.register(r'operacaoitens', OperacaoItemViewSet)

urlpatterns = router.urls