# -*- coding: utf-8 -*-

from django.views.debug import technical_500_response
import sys

class UserBasedExceptionMiddleware(object):
    def process_exception(self, request, exception):
        try:
            if request.user.is_superuser:
                return technical_500_response(request, *sys.exc_info())
        except:
            pass
