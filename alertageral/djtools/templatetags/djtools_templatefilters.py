# -*- coding: utf-8 -*-

from decimal import Decimal
from django import template
from django.contrib.admin.templatetags.admin_list import _boolean_icon
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from djtools.utils import split_thousands, to_ascii
import base64


register = template.Library()


@register.filter
def truncatechars(s, num):
    """
    Truncates a word after a given number of chars  
    Argument: Number of chars to truncate after
    """
    length = int(num)
    string = []
    for word in s.split():
        if len(word) > length:
            string.append(word[:length]+'...')
        else:
            string.append(word)
    return u' '.join(string)

@register.filter
def format_bool(value):
    return _boolean_icon(value)
format_bool.is_safe = True

@register.filter
def format_datetime(value):
    if hasattr(value, 'time'):
        seconds = value.second and u':%s' % value.second or u'' 
        return value.strftime('%d/%m/%Y %H:%M') + seconds 
    else:
        return value.strftime('%d/%m/%Y')
format_datetime.is_safe = True

@register.filter
def format_money(value):
    """
    format_money(1) -> '1,00'
    format_money(1000) -> '1.000,00'
    format_money(1000.99) -> '1.000,99'
    """
    value = str(value)
    if '.' in value:
        reais, centavos = value.split('.')
        if len(centavos) > 2:
            centavos = centavos[0:2]
    else:
        reais = value
        centavos = '00'
    reais = split_thousands(reais)
    return unicode(reais + ',' + centavos)
format_money.is_safe = True

@register.filter(name='format_iterable')
def format_iterable(value):
    """
    format_iterable([1]) -> ''
    format_iterable([1, 2]) -> '1 e 2'
    format_iterable([1, 2, 3]) -> '1, 2 e 3'
    """
    values = [unicode(format_(i)) for i in value]
    if len(value) == 0:
        return _('None').lower()
    if len(value) == 1:
        return values[0]
    else:
        return u'%s %s %s' % (u', '.join(values[:-1]), _('and'), values[-1])
    return value

@register.filter(name='format_daterange')
def format_daterange(value1, value2):
    return u'%s a %s' % (format_datetime(value1), format_datetime(value2))

@register.filter(name='format')
def format_(value):
    """Deixa o ``value`` amigável para visualização."""
    if value in (None, ''):
        return u'-'
    elif isinstance(value, bool):
        return format_bool(value)
    elif value.__class__.__name__ == 'Decimal':
        return format_money(value)
    elif hasattr(value, 'strftime'):
        return format_datetime(value)
    elif hasattr(value, '__iter__'):
        return format_iterable(value)
    else:
        return value
format_.is_safe = True

@register.filter 
def sum_values_by_key(list_of_dicts, key):
    if hasattr(list_of_dicts, 'values'):
        list_of_dicts = list_of_dicts.values()
    return sum(d.get(key, 0) for d in list_of_dicts)

@register.filter
def sum_all_dict_values(dictionary):
    """Soma todos os valores de um dicionário ou de um dicionário de dicionários"""
    sum_ = 0
    if isinstance(dictionary, dict):
        for k, v in dictionary.items():
            if isinstance(v, dict):
                sum_ += sum_all_dict_values(v)   
            else:
                try:
                    sum_ += Decimal(str(v))
                except:
                    sum_ += 0
    return sum_

@register.filter(name='get_ldap_attr')
def get_ldap_attr(dic, key):
    # TODO: mover para a app ldap_backend
    
    from ldap_backend.utils import ad_to_datetime
    
    val = dic.get(key, [''])
    
    if isinstance(val, basestring):
        return val.decode('utf-8')
    
    elif len(val) == 1:
        val = val[0]
        if key == 'thumbnailPhoto':
            return mark_safe(u'<img src="data:image/jpeg;base64,%s"/>' % base64.encodestring(val))
        if key in ['accountExpires', 'pwdLastSet', 'badPasswordTime', 'lastLogonTimestamp']:
            if not val or val in ['0', '9223372036854775807']:
                return u'Nunca'
            else:
                return ad_to_datetime(val)
        if key == 'userAccountControl':
            map_ = {
                '512':    u'Enabled Account',
                '514':    u'Disabled Account',
                '544':    u'Enabled, Password Not Required',
                '546':    u'Disabled, Password Not Required',
                '66048':  u'Enabled, Password Doesn\'t Expire',
                '66050':  u'Disabled, Password Doesn\'t Expire',
                '66080':  u'Enabled, Password Doesn\'t Expire & Not Required',
                '66082':  u'Disabled, Password Doesn\'t Expire & Not Required',
                '262656': u'Enabled, Smartcard Required',
                '262658': u'Disabled, Smartcard Required',
                '262688': u'Enabled, Smartcard Required, Password Not Required',
                '262690': u'Disabled, Smartcard Required, Password Not Required',
                '328192': u'Enabled, Smartcard Required, Password Doesn\'t Expire',
                '328194': u'Disabled, Smartcard Required, Password Doesn\'t Expire',
                '328224': u'Enabled, Smartcard Required, Password Doesn\'t Expire & Not Required',
                '328226': u'Disabled, Smartcard Required, Password Doesn\'t Expire & Not Required',
            }
            return u'%s (%s)' % (val, map_.get(val, u'?'))
        try:
            return val.decode('utf-8').encode('utf-8')
        except:
            return u'??????????'
    
    else: # Múltiplos valores para o atributo
        out = [u'<ul>']
        for v in val:
            out.append(u'<li>%s</li>' % v.decode('utf-8'))
        out.append(u'</ul>')
        return mark_safe(u''.join(out))

@register.filter(name='pop_ldap_attr')
def pop_ldap_attr(dic, key):
    value = get_ldap_attr(dic, key)
    if key in dic:
        dic.pop(key)
    return value

@register.filter
def percentage(quantity, total):
    """Calcula qual o percetual de um valor relativo ao todo"""
    try:
        return float(quantity) / total * 100
    except:
        return 0

@register.filter
def count_entries_in_dictlist(dictlist, args):
    """Conta a quantidade de entradas para os argumentos repassados presentes na lista de dicionários"""
    sum = 0
    arg_list = [arg.strip() for arg in args.split(';')]
    key = arg_list[0]
    value = arg_list[1]

    if isinstance(dictlist, list):
        for dictionary in dictlist:
            for k, v in dictionary.items():
                if k == key and v == value:
                    sum += 1
    return sum

@register.filter
def indice(value, arg):
    """Retorna elemento de lista com indice arg"""
    return value[arg]

@register.filter(name='getattr')
def getattr_(obj, args):
    """ Try to get an attribute from an object.

    Example: {% if block|getattr:"editable,True" %}

    Beware that the default is always a string, if you want this
    to return False, pass an empty second argument:
    {% if block|getattr:"editable," %}
    """
    splitargs = args.split(',')
    try:
        (attribute, default) = splitargs
    except ValueError:
        (attribute, default) = args, ''
    
    try:
        return obj.__getitem__(attribute)
    except:
        pass
    
    try:
        attr = obj.__getattribute__(attribute)
    except AttributeError:
        attr = obj.__dict__.get(attribute, default)
    except:
        attr = default
    
    if hasattr(attr, '__call__'):
        return attr.__call__()
    else:
        return attr

@register.filter(name='ldap_attr')
def ldap_attr(obj):
    if isinstance(obj, list):
        if len(obj) == 1:
            val = obj[0]
            if val:
                return mark_safe(val)
            else:
                return mark_safe('-')
        else:
            out = ['<ol>']
            for i in obj:
                out.append('<li>%s</li>' % i)
            out.append('</ol>')
            return mark_safe(''.join(out))
    else:
        if obj:
            return mark_safe(obj)
        else:
            return mark_safe('-')

@register.filter(name='getkey')
def getkey(value, arg):
    return value.get(arg, '')

@register.filter
def in_group(user, group):
    """Returns True/False if the user is in the given group(s).
    Usage:
        {% if user|in_group:"GroupX" %}
        or
        {% if user|in_group:"GroupX,A group with white-spaces" %}
    You can specify a single group or comma-delimited list.
    """
    if isinstance(group, basestring):
        group_list = [g.strip() for g in group.split(',')]
    elif isinstance(group, list):
        group_list = [g.strip() for g in group]
    return user.groups.filter(name__in=group_list).count()
in_group.is_safe = True

@register.filter
def calc_colspan(max_pairs, pairs):
    return 2*(int(max_pairs) - int(pairs)) + 1

@register.filter
def span_observacao(value):
    if value:
        return mark_safe('<span class="observacao">%s</span>' % (value))
    else:
        return ''


@register.filter
def status(value):
    if value:
        css = to_ascii(value.lower().replace(' ', '-')) 
        return mark_safe(u'<span class="status status-%s">%s</span>' % (css, value))
    else:
        return u''

