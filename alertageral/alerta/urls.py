from django.conf.urls import patterns, include, url
from django.conf import settings

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('alerta.views',
    (r'todosalertas', 'todosalertas'),
    (r'cadastro', 'cadastro'),
    (r'recupera_senha', 'recupera_senha'),
    (r'cadastrar_alerta', 'cadastrar_alerta'),
)