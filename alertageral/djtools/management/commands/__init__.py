# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
import logging

class BaseCommandPlus(BaseCommand):
    
    """
    A classe ``BaseCommandPlus`` deve ser usada no lugar da 
    ``django.core.management.base.BaseCommand`` para que um email seja enviado 
    em caso de erro na execução do comando.
    """
    
    def execute(self, *args, **options):
        try:
            super(BaseCommandPlus, self).execute(*args, **options)
        except Exception, e:
            logger = logging.getLogger('django.utils.log.AdminEmailHandler')
            logger.exception(msg=self.__class__.__module__)
    