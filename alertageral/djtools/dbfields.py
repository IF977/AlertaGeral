# -*- coding: utf-8 -*-

from django import utils as django_utils
from django.conf import settings
from django.contrib.auth.models import User
from localflavor.br.br_states import STATE_CHOICES
from django.db import models
from djtools import formfields
from djtools.utils import to_ascii, eval_attr, get_tl

class CharFieldPlus(models.CharField):
    
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 255)
        self.widget_attrs = kwargs.pop('widget_attrs', {})
        if 'width' in kwargs:
            self.widget_attrs['style'] = 'width: %spx;' % kwargs.pop('width')
        super(CharFieldPlus, self).__init__(*args, **kwargs)
    
    def formfield(self, *args, **kwargs):
        field = super(CharFieldPlus, self).formfield(*args, **kwargs)
        field.widget.attrs.update(self.widget_attrs)
        return field

    
class IntegerFieldPlus(models.IntegerField):
    def formfield(self, *args, **kwargs):
        field = super(IntegerFieldPlus, self).formfield(*args, **kwargs)
        field.widget.attrs['style'] = 'width: 30px;'
        return field
    
class PositiveIntegerFieldPlus(models.PositiveIntegerField):
    def formfield(self, *args, **kwargs):
        field = super(PositiveIntegerFieldPlus, self).formfield(*args, **kwargs)
        field.widget.attrs['style'] = 'width: 30px;'
        return field

class ForeignKeyPlus(models.ForeignKey):
    """
    Deixa o widget padrão o ModelChoiceFieldPlus quando se tem mais de 50 registros.
    """
    def formfield(self, **kwargs):
        if self.rel.to._default_manager.count() > 50:
            kwargs.setdefault('form_class', formfields.ModelChoiceFieldPlus)
        return super(self.__class__, self).formfield(**kwargs)
    
class OneToOneFieldPlus(models.OneToOneField):
    """
    Deixa o widget padrão o ModelChoiceFieldPlus.
    """
    def formfield(self, **kwargs):
        kwargs.setdefault('form_class', formfields.ModelChoiceFieldPlus)
        return super(self.__class__, self).formfield(**kwargs)

class ManyToManyFieldPlus(models.ManyToManyField):
    """
    Deixa o widget padrão o MultipleModelChoiceFieldPlus.
    """
    def __formfield(self, **kwargs):
        kwargs.setdefault('form_class', formfields.MultipleModelChoiceFieldPlus)
        return super(self.__class__, self).formfield(**kwargs)

class CurrentUserField(models.ForeignKey):
    """
    Utilizado para armazenar o usuário autenticado.
    """
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('editable', False)
        kwargs.setdefault('null', True)
        kwargs.setdefault('blank', True)
        kwargs.setdefault('to', User)
        kwargs.setdefault('default', get_tl().get_user)
        super(CurrentUserField, self).__init__(*args, **kwargs)

class SearchField(models.TextField):
    
    """
    Campo utilizado para buscas, recebendo uma lista de atributos da instância 
    (``attrs``) e os convertendo para valores de forma (``prepare_string``) a 
    tornar as buscas mais eficientes.
    """
    
    @staticmethod
    def prepare_string(v):
        return unicode(to_ascii(v).upper().strip())
    
    def pre_save(self, model_instance, add):
        search_text = []
        for attr_name in self.search_attrs:
            val = eval_attr(model_instance, attr_name)
            if val: # Evitar string `NONE`
                val = self.prepare_string(val)
                search_text.append(val)
        return u' '.join(search_text)
    
    def __init__(self, *args, **kwargs):
        if 'attrs' in kwargs:
            self.search_attrs = kwargs.pop('attrs')
        kwargs.setdefault('blank', True)
        kwargs.setdefault('default', u'')
        kwargs.setdefault('editable', False)
        super(SearchField, self).__init__(*args, **kwargs)

class BrSexoField(models.CharField):
    
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 1)
        kwargs.setdefault('choices', (('M', 'Masculino'), ('F', 'Feminino')))
        super(self.__class__, self).__init__(*args, **kwargs)

class BrDiaDaSemanaField(models.CharField):

    choices = [(unicode(django_utils.dates.WEEKDAYS[i]), 
                unicode(django_utils.dates.WEEKDAYS[i])) for i in range(7)]

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 50)
        kwargs.setdefault('choices', self.choices)
        super(BrDiaDaSemanaField, self).__init__(*args, **kwargs)

class DecimalFieldPlus(models.DecimalField):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('decimal_places', 2)
        kwargs.setdefault('max_digits', 12)
        super(self.__class__, self).__init__(*args, **kwargs)
    
    def formfield(self, **kwargs):
        kwargs.setdefault('form_class', formfields.DecimalFieldPlus)
        return super(self.__class__, self).formfield(**kwargs)

class PostgresBinaryField(models.Field):
    
    def db_type(self, connection):
        return 'bytea'
    
    def get_db_prep_value(self, value, connection, prepared=False):
        if value:
            import psycopg2
            if isinstance(value, file):
                file_ = value
                value = file_.read()
                file_.close()
            return psycopg2.Binary(value)
        else:
            return value

class BrCpfField(models.CharField):
    
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 14)
        kwargs.setdefault('verbose_name', u'CPF')
        super(self.__class__, self).__init__(*args, **kwargs)
    
    def formfield(self, **kwargs):
        kwargs.setdefault('form_class', formfields.BrCpfField)
        return super(self.__class__, self).formfield(**kwargs)

class BrCnpjField(models.CharField):
    
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 18)
        kwargs.setdefault('verbose_name', u'CNPJ')
        super(self.__class__, self).__init__(*args, **kwargs)
    
    def formfield(self, **kwargs):
        kwargs.setdefault('form_class', formfields.BrCnpjField)
        return super(self.__class__, self).formfield(**kwargs)

class BrCepField(models.CharField):
    
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 9)
        super(self.__class__, self).__init__(*args, **kwargs)
    
    def formfield(self, **kwargs):
        kwargs.setdefault('form_class', formfields.BrCepField)
        return super(self.__class__, self).formfield(**kwargs)

class BrTelefoneField(models.CharField):
    
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 14)
        super(self.__class__, self).__init__(*args, **kwargs)
    
    def formfield(self, **kwargs):
        kwargs.setdefault('form_class', formfields.BrTelefoneField)
        return super(self.__class__, self).formfield(**kwargs)

class DateFieldPlus(models.DateField):
    
    def formfield(self, *args, **kwargs):
        kwargs.setdefault('form_class', formfields.DateFieldPlus)
        field = super(DateFieldPlus, self).formfield(**kwargs)
        field.widget.attrs.setdefault('style', 'width: 75px;')
        return field

class DateTimeFieldPlus(models.DateTimeField):
    
    def formfield(self, **kwargs):
        kwargs.setdefault('form_class', formfields.DateTimeFieldPlus)
        return super(self.__class__, self).formfield(**kwargs)

class BrEstadoBrasileiroField(models.CharField):
    
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 2)
        kwargs.setdefault('choices', STATE_CHOICES)
        super(self.__class__, self).__init__(*args, **kwargs)

if 'south' in settings.INSTALLED_APPS:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([
            (
                [SearchField],
                [],
                {
                    "attrs": ["search_attrs", {}],
                },
            ),
        ], ["^djtools\.dbfields\.SearchField"])
    add_introspection_rules([], ["^djtools\.dbfields\.CharFieldPlus"])
    add_introspection_rules([], ["^djtools\.dbfields\.IntegerFieldPlus"])
    add_introspection_rules([], ["^djtools\.dbfields\.PositiveIntegerFieldPlus"])
    add_introspection_rules([], ["^djtools\.dbfields\.ForeignKeyPlus"])
    add_introspection_rules([], ["^djtools\.dbfields\.OneToOneFieldPlus"])
    add_introspection_rules([], ["^djtools\.dbfields\.ManyToManyFieldPlus"])
    add_introspection_rules([], ["^djtools\.dbfields\.CurrentUserField"])
    add_introspection_rules([], ["^djtools\.dbfields\.BrSexoField"])
    add_introspection_rules([], ["^djtools\.dbfields\.BrDiaDaSemanaField"])
    add_introspection_rules([], ["^djtools\.dbfields\.DecimalFieldPlus"])
    add_introspection_rules([], ["^djtools\.dbfields\.PostgresBinaryField"])
    add_introspection_rules([], ["^djtools\.dbfields\.BrCpfField"])
    add_introspection_rules([], ["^djtools\.dbfields\.BrCnpjField"])
    add_introspection_rules([], ["^djtools\.dbfields\.BrCepField"])
    add_introspection_rules([], ["^djtools\.dbfields\.BrTelefoneField"])
    add_introspection_rules([], ["^djtools\.dbfields\.DateFieldPlus"])
    add_introspection_rules([], ["^djtools\.dbfields\.DateTimeFieldPlus"])
    add_introspection_rules([], ["^djtools\.dbfields\.BrEstadoBrasileiroField"])

