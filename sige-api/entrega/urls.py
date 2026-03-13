from rest_framework.routers import DefaultRouter
from .views import (
    EntregaViewSet,
    ItemEntregaViewSet,
    PedidosDaOrdemViewSet
)

router = DefaultRouter()
router.register(r'entregas/pedidos', PedidosDaOrdemViewSet, basename='pedidos-da-ordem')
router.register(r'entregas',EntregaViewSet)
router.register(r'itementregas', ItemEntregaViewSet)

urlpatterns = router.urls