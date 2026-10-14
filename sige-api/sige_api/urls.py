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
from django.conf import settings
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve

urlpatterns = [
    # As fotos dos gêneros são poucas e pequenas; o próprio Django as serve,
    # inclusive em produção (o Nginx encaminha /media/ para a API).
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    path('admin/', admin.site.urls),
    path('api/v1/', include('cadastro.urls')),
    path('api/v1/', include('empenho.urls')),
    path('api/v1/', include('entrega.urls')),
    path('api/v1/', include('licitacao.urls')),
    path('api-auth/', include('rest_framework.urls')),
    path('api/v1/', include('usuario.urls')),
    path('api/v1/', include('estoque.urls')),
    path('api/v1/', include('cardapio.urls')),
]
