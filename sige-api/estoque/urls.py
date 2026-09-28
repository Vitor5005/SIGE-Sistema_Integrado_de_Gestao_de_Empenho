from rest_framework.routers import DefaultRouter

from estoque.views import EstoqueViewSet, MovimentacaoEstoqueViewSet, PainelNutricionistaViewSet


router = DefaultRouter()
router.register(r'estoques', EstoqueViewSet, basename='estoque')
router.register(r'movimentacoes-estoque', MovimentacaoEstoqueViewSet, basename='movimentacao-estoque')
router.register(r'painel-nutricionista', PainelNutricionistaViewSet, basename='painel-nutricionista')

urlpatterns = router.urls
