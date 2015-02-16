from django.conf.urls import patterns, include, url
from django.conf import settings

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('alerta.views',
    (r'todosalertas', 'todosalertas'),
    (r'recentes_alertas', 'recentes_alertas'),
    (r'cadastro', 'cadastro'),
    (r'recupera_senha', 'recupera_senha'),
    (r'cadastrar_alerta', 'cadastrar_alerta'),
    (r'comentarios/(?P<alerta_id>\d+)$', 'comentarios'),
    (r'validar_responder_alerta/(?P<alerta_id>\d+)$', 'validar_responder_alerta'),
    (r'responder_alerta/(?P<alerta_id>\d+)$', 'responder_alerta'),
)