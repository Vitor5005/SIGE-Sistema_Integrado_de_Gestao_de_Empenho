from rest_framework.routers import DefaultRouter

from estoque.views import EstoqueViewSet, MovimentacaoEstoqueViewSet


router = DefaultRouter()
router.register(r'estoques', EstoqueViewSet, basename='estoque')
router.register(r'movimentacoes-estoque', MovimentacaoEstoqueViewSet, basename='movimentacao-estoque')

urlpatterns = router.urls
