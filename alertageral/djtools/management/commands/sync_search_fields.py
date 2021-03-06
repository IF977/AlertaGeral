# -*- coding: utf-8 -*-

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import models
from djtools.utils import get_search_field

class Command(BaseCommand):

    def handle(self, *args, **options):
        """
        Preenche os campos SearchField automaticamente (invocando o método `save`).
        O normal é salvar apenas as instâncias que não tenham o campo SeachField preenchido;
        caso deseje salvar todas as instâncias, passe o parâmetro `all`.
        """
        for app in settings.INSTALLED_APPS:
            try:
                app = models.get_app(app)
            except:
                continue
            model_classes = models.get_models(app)
            for model_class in model_classes:
                if get_search_field(model_class):
                    print self.style.SQL_KEYWORD('Syncronizing %s class...' % model_class.__name__)
                    if 'all' in args:
                        items = model_class.objects.all()
                    else:
                        args = {get_search_field(model_class).name: ''}
                        items = model_class.objects.filter(**args)
                    for model_instance in items:
                        models.Model.save(model_instance)
        print self.style.SQL_COLTYPE('Sync SearchFields finished.')
