# -*- coding: utf-8 -*-

from django.conf import settings
from django.conf.urls import *
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
import os

admin.autodiscover()
admin.autodiscover()

handler500 = 'django.views.defaults.server_error'
handler404 = 'django.views.defaults.page_not_found'

urlpatterns = patterns('',
    
    (r'^admin/', include(admin.site.urls)),
    (r'^media/(.*)$', 'django.views.static.serve',
     {'document_root': settings.MEDIA_ROOT}),
    (r'^static/(.*)$', 'django.views.static.serve',
     {'document_root': settings.STATIC_ROOT}),
    (r'^accounts/login/$', 'django.contrib.auth.views.login',
     {'template_name': 'templates/login.html'}),
    (r'^admin/logout/$', 'django.contrib.auth.views.logout',
     {'next_page': '/'}),
    (r'^logout/', 'django.contrib.auth.views.logout',
     {'next_page': '/'})
)

# Include de cada app instalada
for app in settings.INSTALLED_APPS:
    if not app.startswith('django.'):
        if os.path.exists(os.path.join(settings.PROJECT_PATH, '%s/urls.py' % (app))):
            urlpatterns += patterns('',
                (r'^%s/' % (app), include('%s.urls' % (app)) ),
            )

urlpatterns += patterns('views',
    # Geral
    (r'^$', 'index'),
)