from rest_framework.routers import DefaultRouter
from .views import (
    EnderecoViewSet,
    FornecedorViewSet,
    ItemGenericoViewSet
)

router = DefaultRouter()

router.register(r'enderecos', EnderecoViewSet)
router.register(r'fornecedores', FornecedorViewSet)
router.register(r'itemgenericos', ItemGenericoViewSet)

urlpatterns = router.urls