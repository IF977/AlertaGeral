# -*- coding: utf-8 -*-

from django.contrib.auth.models import Group
from django.db import models
from djtools.dbfields import SearchField
from djtools.utils import get_search_field
from operator import or_


def _search(cls, q, fields=None, max_fields=5):
    """
    Busca genérica para models.
    
    q         : string a ser buscada
    fields    : define os campos que se quer filtrar
    max_fields: usado quando não é passado o fields e define os N primeiros campos
                charfield do modelo que serão incluídos na busca
    """
    
    def _get_str_fields(cls):
        """Retorna lista de campos (string) cujo tipo é CharField ou TextField"""
        fields = []
        for f in cls._meta.fields:
            if f.get_internal_type() in ['CharField', 'TextField']:
                fields.append(f.name)
        if not fields:
            raise Exception(u'Class %s don\'t have CharField or TextField.' % cls.__name__)
        return fields
    
    search_field = get_search_field(cls)
    
    if search_field and not fields:
        use_fields = False
        use_search_field = True
    else:
        use_fields = True
        use_search_field = False
    
    qs = cls.objects.all()
    
    if use_fields:
        fields = fields or _get_str_fields(cls)[:max_fields]
        for word in q.split(' '):
            or_queries = [models.Q(
                **{'%s__icontains' % field_name: word}) for field_name in fields]
            qs = qs.filter(reduce(or_, or_queries))
    elif use_search_field:
        q = SearchField.prepare_string(q)
        for word in q.split(' '):
            or_queries = [models.Q(**{'%s__contains' % search_field.name: word})]
            qs = qs.filter(reduce(or_, or_queries))
    
    return qs
        

class ModelPlus(models.Model):
    """ A models.Model with facilities """
    
    class Meta:
        abstract = True
    
    def __unicode__(self):
        for f in self.__class__._meta.fields:
            if f.get_internal_type() in ['CharField', 'TextField']:
                return getattr(self, f.name)
        return u'%s #d' % (self.__class__._meta.verbose_name, self.pk)
    
    @classmethod
    def search(cls, q, fields=None, max_fields=5):
        return _search(cls, q, fields=fields, max_fields=max_fields)
    
    @classmethod
    def get_or_create(cls, fill_attr=None, **kwargs):
        """ A short to objects.get_or_create
        By pass the kwargs arguments to objects.get_or_create class method, 
        if its has created the object, this get_or_create will filled the fill_attr attribute, if is not None,
        with a message to update the objects.
        If fill_attr is None it will fill the first null char (or text) field.
        """
    
        def get_first_null_char_field(self, force_attr=None):
            
            if force_attr:
                return self._meta.get_field(force_attr)
            
            for f in self._meta.fields:
                if f.get_internal_type() in ['CharField', 'TextField'] and not getattr(self, f.name):
                    return f
            
            return None

        o, created = cls.objects.get_or_create(**kwargs)
        if created:
            f = get_first_null_char_field(o, fill_attr)
            if f:
                c = u'Atualize o cadastro de %s' % cls._meta.verbose_name_plural
                c = c[:f.max_length]
                setattr(o, f.name, c)
                o.save()
            
        return o, created


class GroupManagement(models.Model):
    manager_group = models.ForeignKey(Group, related_name='groupmanagement_manager_set')
    managed_groups = models.ManyToManyField(Group, related_name='groupmanagement_managed_set')
    
    class Meta:
        verbose_name = u"Gerenciamento de Grupo"
        verbose_name_plural = u"Gerenciamento de Grupos"
    
    def __unicode__(self):
        return u"%s" % self.manager_group.name

    @classmethod
    def user_can_manage(cls, user):
        return user.is_superuser or cls.objects.filter(manager_group__in=user.groups.all()).count()

