from django.conf.urls import patterns, url

from registration.views import register

urlpatterns = patterns('',
    url(
        r'^register/$',
        register,
        {'backend': 'captcha.backends.default.CaptchaDefaultBackend'},
        name='registration_register'
    ),
)
