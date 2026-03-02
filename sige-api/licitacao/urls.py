from rest_framework.routers import DefaultRouter
from .views import (
    ItensDaAtaViewSet,
    LicitacaoViewSet,
    AtaViewSet,
    ItemAtaViewSet,
    ValorDoEmpenhoViewSet
)

router = DefaultRouter()

router.register(r'licitacoes',LicitacaoViewSet)
router.register(r'atas/itens_da_ata', ItensDaAtaViewSet, basename='itens_da_ata')
router.register(r'atas/empenho', ValorDoEmpenhoViewSet, basename='valor_empenho')
router.register(r'atas', AtaViewSet)
router.register(r'itematas', ItemAtaViewSet)



urlpatterns = router.urls