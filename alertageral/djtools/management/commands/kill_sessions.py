# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from django.conf import settings
from django.core.management.base import BaseCommand
from time import mktime
import os

"""
Remove arquivos de sessão sem modificação nas últimas 24 horas.
"""

def datetime_to_ordinal(datetime_):
    return mktime(datetime_.timetuple())

def ordinal_to_datetime(ordinal_):
    return datetime.fromtimestamp(ordinal_)

class Command(BaseCommand):

    def handle(self, *args, **options):
        _24_hours_ago = datetime_to_ordinal(datetime.now() - timedelta(1))
        total_files, removed_files = 0, 0
        for file_ in [i for i in os.listdir(settings.SESSION_FILE_PATH) \
                      if i.startswith('sessionid')]:
            total_files += 1
            file_path = os.path.join(settings.SESSION_FILE_PATH, file_)
            mtime = os.path.getmtime(file_path)
            if mtime < _24_hours_ago:
                os.remove(file_path)
                removed_files += 1 
        print self.style.SQL_COLTYPE('%d/%d sessions killed' % (removed_files, 
                                                                total_files))
    