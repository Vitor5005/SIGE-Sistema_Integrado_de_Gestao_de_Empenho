from rest_framework.routers import DefaultRouter
from .views import (
    LicitacaoViewSet,
    AtaViewSet,
    ItemAtaViewSet,
    ValorDoEmpenhoViewSet
)

router = DefaultRouter()

router.register(r'licitacoes',LicitacaoViewSet)
router.register(r'atas', AtaViewSet)
router.register(r'itematas', ItemAtaViewSet)
router.register(r'ata/valor_empenho', ValorDoEmpenhoViewSet, basename='valor_empenho')


urlpatterns = router.urls