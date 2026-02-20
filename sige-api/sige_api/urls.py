"""
URL configuration for sige_api project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
# from rest_framework.routers import DefaultRouter
# from cadastro.views import EnderecoViewSet, FornecedorViewSet, ItemGenericoViewSet
# from licitacao.views import LicitacaoViewSet, AtaViewSet, ItemAtaViewSet
# from entrega.views import EntregaViewSet, ItemEntregaViewSet 
# from empenho.views import EmpenhoViewSet, ItemEmpenhoViewSet, OperacaoItemViewSet


# router = DefaultRouter()
# router.register(r'enderecos', EnderecoViewSet)
# router.register(r'fornecedores', FornecedorViewSet)
# router.register(r'itens-genericos', ItemGenericoViewSet)
# router.register(r'licitacoes', LicitacaoViewSet)
# router.register(r'atas', AtaViewSet)
# router.register(r'itens-ata', ItemAtaViewSet)
# router.register(r'entregas', EntregaViewSet)
# router.register(r'itens-entrega', ItemEntregaViewSet)
# router.register(r'empenhos', EmpenhoViewSet)
# router.register(r'itens-empenho', ItemEmpenhoViewSet)
# router.register(r'operacoes-item', OperacaoItemViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('cadastro.urls')),
    path('api/v1/', include('empenho.urls')),
    path('api/v1/', include('entrega.urls')),
    path('api/v1/', include('licitacao.urls')),
    path('api-auth/', include('rest_framework.urls')),
    #path('', include(router.urls))
]
