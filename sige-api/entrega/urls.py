from rest_framework.routers import DefaultRouter
from .views import (
    EntregaViewSet,
    ItemEntregaViewSet,
)

router = DefaultRouter()
router.register(r'entregas',EntregaViewSet)
router.register(r'itementregas', ItemEntregaViewSet)

urlpatterns = router.urls