# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.conf import settings
from os.path import isfile
from xml.dom import minidom
from django.contrib.auth.models import Permission

def getText(nodelist):
    rc = ""
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc = rc + node.data
    return rc

class Command(BaseCommand):
    def handle(self, *args, **options):
        #import ipdb; ipdb.set_trace();
        # O trecho abaixo é necessário para funcionar no django 1.0.4
        apps = []
        if len(args):
            for arg in args:
                if arg[0:3] == 'app':
                    apps = arg.split('=')[1].split(',')
        for app in settings.INSTALLED_APPS:
            self.processMenuPermission(app, apps, options)
    
    def processMenuPermission(self, app, apps, options):
        #import ipdb; ipdb.set_trace()
        if len(apps) == 0 or app in apps:
            if isfile('%s/menu.xml' % app) and (len(apps) == 0 or app in apps):
                dom = minidom.parse('%s/menu.xml' % app).documentElement
                for item in dom.getElementsByTagName("item"):
                    for require in item.getElementsByTagName("requires"):
                        for permission in require.getElementsByTagName("permission"):
                            permission = getText(permission.childNodes)
                            if "." in permission: #Procura a permissão no banco caso a aplicação e a permissão estejam definidas
                                appname = permission.split('.')[0]
                                permission = permission.split('.')[1]                                
                                if Permission.objects.filter(content_type__app_label=appname, codename=permission).count() == 0:
                                    print self.style.ERROR_OUTPUT(u"ERRO: permissao --- " + appname + "." + permission + " --- nao encontrada na base de dados") + " =======> ARQUIVO: " + '%s/menu.xml' % app
                            else: #falta especificar o nome da aplicação 
                                print self.style.ERROR_OUTPUT(u"ERRO: aplicacao nao definida --- " + permission) + " =======> ARQUIVO: " + '%s/menu.xml' % app