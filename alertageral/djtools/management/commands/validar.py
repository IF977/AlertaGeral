# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.db import models
from pprint import pprint

class Command(BaseCommand):

    def handle(self, *args, **options):
        
        expected_perms = []
        for model in models.get_models():
            for perm_codename in [p[0] for p in model._meta.permissions]:
                expected_perms.append(u'%s.%s' % (model._meta.app_label, perm_codename))
            for p in ('add', 'change', 'delete'):
                expected_perms.append(u'%s.%s_%s' % (model._meta.app_label, p, model.__name__.lower()))
        database_perms = []
        for app_label, perm_codename in models.get_model('auth', 'Permission').objects.values_list('content_type__app_label', 'codename'):
            database_perms.append(u'%s.%s' % (app_label, perm_codename))
        set1 = set(database_perms) - set(expected_perms)
        print len(set1), 'permissions found at database, but not defined in any model permissions attribute'
        pprint(sorted(set1))
        