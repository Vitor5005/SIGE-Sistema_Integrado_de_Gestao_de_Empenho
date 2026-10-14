from rest_framework.routers import DefaultRouter

from cardapio.views import CardapioViewSet

router = DefaultRouter()
router.register(r'cardapios', CardapioViewSet, basename='cardapio')

urlpatterns = router.urls
