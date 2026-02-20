from rest_framework.routers import DefaultRouter
from .views import (
    LicitacaoViewSet,
    AtaViewSet,
    ItemAtaViewSet
)

router = DefaultRouter()

router.register(r'licitacoes',LicitacaoViewSet)
router.register(r'atas', AtaViewSet)
router.register(r'itematas', ItemAtaViewSet)

urlpatterns = router.urls