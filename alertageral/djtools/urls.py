# -*- coding: utf-8 -*-

from django.conf.urls.defaults import *

urlpatterns = patterns('djtools.views',
    (r'^give_permission/$', 'give_permission'),
    (r'^delete_object/(?P<app>\w+)/(?P<model>\w+)/(?P<pk>\d+)/$', 'delete_object'),
    (r'^breadcrumbs_reset/(?P<menu_item_id>\w+)/(?P<url>.*)$', 'breadcrumbs_reset'),
    (r'^notificar_grupo/(?P<pk_grupo>\d+)/$', 'notificar_grupo'),
    
    (r'^permissions/(?P<app>\w+)/$', 'permissions')
)

urlpatterns += patterns('djtools.ext_fields',
    (r'^autocomplete/(?P<app_name>\w+)/(?P<class_name>\w+)/$', 'autocomplete_view'),
)