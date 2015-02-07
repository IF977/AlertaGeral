# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):

    def handle(self, *args, **options):
        User.objects.update(password=r'sha1$f629f$074a22704caf5c8499e338fd9f618964e6d39edd')
        print self.style.SQL_COLTYPE('%d passwords changed to "123"' % User.objects.count())
