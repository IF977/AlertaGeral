# -*- coding: utf-8 -*-

"""
``APP/permissions.xml`` template:

<groups>
    <group>
        <name>suap_operador</name>
        <models>
            <model>
                <app>comum</app>
                <name>sala</name>
                <permissions>
                    <permission>can_add_sala</permission>
                    <permission>can_change_sala</permission>
                    <permission>can_delete_sala</permission>
                </permissions>
            </model>
        </models>
    </group>
</groups>
"""

from django.core.management.base import BaseCommand
from djtools.management.permission import GroupPermission
from djtools.utils import sync_groups_and_permissions
from django.conf import settings
from os.path import isfile
from djtools.models import GroupManagement
from django.contrib.auth.models import Group

class Command(BaseCommand):
    
    """
    https://docs.djangoproject.com/en/1.3/ref/django-admin/#django-admin-option---verbosity
    Use --verbosity to specify the amount of notification and debug information that django-admin.py should print to the console.
        0 means no output.
        1 means normal output (default).
        2 means verbose output.
        3 means very verbose output.
    """

    def handle(self, *args, **options):
        # O trecho abaixo é necessário para funcionar no django 1.0.4
        options['verbosity'] = options.get('verbosity', '1')
        apps = []
        if len(args):
            for arg in args:
                if arg[0:3] == 'app':
                    apps = arg.split('=')[1].split(',')
        for app in settings.INSTALLED_APPS:
            self.processGroupPermission(app, apps, options)
        if options['verbosity'] != '0':
            print self.style.SQL_COLTYPE('[sync_permissions] finished')
    
    def processGroupPermission(self, app, apps, options):
        if len(apps) == 0 or app in apps:
            if isfile('%s/permissions.xml' % app) and (len(apps) == 0 or app in apps):
                if options['verbosity'] in ('2', '3'):
                    print self.style.SQL_KEYWORD('Processing %s' % ('%s/permissions.xml' % app))
                groupPermission = GroupPermission(app)
                groupPermission.process('%s/permissions.xml' % app)
                sync_groups_and_permissions(groupPermission.getDict())
                self.processGroupManagement(groupPermission)
                
    def processGroupManagement(self, groupPermission):
        app = groupPermission.getAppName()
        group, group_created = Group.objects.get_or_create(name=u'%s Administrador' % app)
        groups = groupPermission.getGroups()
        gm, criado = GroupManagement.objects.get_or_create(manager_group=group)
        gm.managed_groups.clear()
        for g in groups:
            gm.managed_groups.add(Group.objects.get(name=g.getName().strip()))
        gm.managed_groups.add(group)
        