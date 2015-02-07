# -*- coding: utf-8 -*-

from datetime import date, datetime, timedelta
from decimal import Decimal
from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import Group, Permission
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.db.models.fields import AutoField
from django.forms import ValidationError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext, TemplateDoesNotExist
from django.utils import simplejson
from django.utils.datastructures import SortedDict
from django.utils.encoding import smart_str
from django.utils.safestring import mark_safe
from itertools import islice, chain
from operator import or_, itemgetter
from random import choice
from unicodedata import normalize
import base64
import cPickle
import csv
import logging
import os
import re
import warnings
import zlib


class EnumBase(type):
    """
    Adiciona os atributos ``choices`` e ``choices_flat`` para Classes filhas de
    Enum.
    Nota: Esta é uma classe interna e só deve ser usada no ``Enum``.
    """
    def __new__(cls, name, bases, attrs):
        super_new = super(EnumBase, cls).__new__
        module = attrs.pop('__module__')
        new_class = super_new(cls, name, bases, {'__module__': module})
        choices, choices_flat = [], []
        for key, val in attrs.items():
            if type(val) in [unicode, basestring, int, float]:
                choices.append([val, val])
                choices_flat.append(val)
            setattr(new_class, key, val)
        setattr(new_class, 'choices', choices)
        setattr(new_class, 'choices_flat', choices_flat)
        return new_class
    

class Enum(object):
    """
    Enumerador que deve ser utilizado para choices.
        class MeuChoice(Enum):
            CHOICE_A = u'ChoiceA'
            CHOICE_B = u'ChoiceB'
        >>> MeuChoice.choices
        >>> [[u'ChoiceA',u'ChoiceA'], [u'ChoiceB', u'ChoiceB']]
        >>> MeuChoice.choices_flat
        >>> [u'ChoiceA', u'ChoiceB']
    """
    __metaclass__ = EnumBase
    choices = None # será modificado no __new__ de EnumBase
    chocies_flat = None # será modificado no __new__ de EnumBase

class BrModelAdmin(admin.ModelAdmin):
    
    def formfield_for_dbfield(self, db_field, **kwargs):
        # TODO: automatizar esta função
        
        from djtools.dbfields import BrCpfField, BrCepField, BrTelefoneField, DecimalFieldPlus
        from djtools.formwidgets import BrDataWidget, BRCpfWidget, BrCepWidget, BrTelefoneWidget, BrDinheiroWidget
        
        if isinstance(db_field, models.DateField): # DateField
            kwargs['widget'] = BrDataWidget
            return db_field.formfield(**kwargs)
        if isinstance(db_field, BrCpfField): # CPF

            kwargs['widget'] = BRCpfWidget
            return db_field.formfield(**kwargs)
        if isinstance(db_field, BrCepField): # CEP

            kwargs['widget'] = BrCepWidget
            return db_field.formfield(**kwargs)
        if isinstance(db_field, BrTelefoneField): # CEP
            kwargs['widget'] = BrTelefoneWidget
            return db_field.formfield(**kwargs)
        if isinstance(db_field, DecimalFieldPlus): # DecimalFieldPlus
            kwargs['widget'] = BrDinheiroWidget
            return db_field.formfield(**kwargs)
        return super(BrModelAdmin, self).formfield_for_dbfield(db_field, **kwargs)

class BrTabularInline(admin.TabularInline):

    def formfield_for_dbfield(self, db_field, **kwargs):
        # TODO: automatizar esta função
        
        from djtools.dbfields import BrCpfField, BrCepField, BrTelefoneField, DecimalFieldPlus
        from djtools.formwidgets import BrDataWidget, BRCpfWidget, BrCepWidget, BrTelefoneWidget, BrDinheiroWidget
        
        if isinstance(db_field, models.DateField): # DateField
            kwargs['widget'] = BrDataWidget
            return db_field.formfield(**kwargs)
        if isinstance(db_field, BrCpfField): # CPF

            kwargs['widget'] = BRCpfWidget
            return db_field.formfield(**kwargs)
        if isinstance(db_field, BrCepField): # CEP

            kwargs['widget'] = BrCepWidget
            return db_field.formfield(**kwargs)
        if isinstance(db_field, BrTelefoneField): # CEP
            kwargs['widget'] = BrTelefoneWidget
            return db_field.formfield(**kwargs)
        if isinstance(db_field, DecimalFieldPlus): # DecimalFieldPlus
            kwargs['widget'] = BrDinheiroWidget
            return db_field.formfield(**kwargs)
        return super(BrTabularInline, self).formfield_for_dbfield(db_field, **kwargs)


class JsonResponse(HttpResponse):
    def __init__(self, data):
        content=simplejson.dumps(data)
        HttpResponse.__init__(self, content=content,
                              mimetype='application/json')

class PdfResponse(HttpResponse):
    
    def __init__(self, content, name=u'relatorio', attachment=True):
        HttpResponse.__init__(self, content, mimetype='application/pdf')
        if attachment:
            self['Content-Disposition'] = 'attachment; filename="%s.pdf"' \
                % name.encode('utf-8')

def human_str(val, encoding='utf-8', blank=u''):
    """
    Retorna uma representação humana para o objeto.
    
    human_basestring(True) -> 'Sim'
    human_basestring(False) -> 'Não'
    human_basestring(User.objects.get(id=1)) -> 'admin'
    human_basestring(None) -> ''
    human_basestring(None, blank=u'-') -> '-'
    human_basestring(u'Teste') -> 'Teste'
    human_basestring('Teste') -> 'Teste'
    """
    if val is None:
        val = blank
    elif not isinstance(val, basestring): # Não é uma string
        if isinstance(val, bool):
            val = val and u'Sim' or u'Não'
        elif hasattr(val, 'strftime'):
            if hasattr(val, 'time'):
                val = val.strftime('%d/%m/%Y %H:%M:%S')
            else:
                val = val.strftime('%d/%m/%Y')
        else:
            val = unicode(val)
    elif isinstance(val, basestring) and not isinstance(val, unicode):
        # Assume que passou uma string na codificação correta (``encoding``)
        return val
    return val.encode(encoding, 'replace')


def CsvResponse(rows, name=u'report', attachment=True, encoding='utf-8', 
                value_for_none=u'-'):
    """
    Retorna uma resposta no formato csv. ``rows`` deve ser lista de listas cujos 
    valores serão convertidos com ``human_str``.
    """
    if not isinstance(rows, list) or \
        (len(rows) and not isinstance(rows[0], list)):
        raise ValueError('``rows`` must be a list of lists')
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename="%s.csv"' \
        % name.encode('utf-8')
    writer = csv.writer(response)
    for row in rows:
        row = [human_str(i, encoding=encoding, blank=u'-') for i in row]
        writer.writerow(row)
    return response

def XlsResponse(rows, name=u'report', attachment=True, encoding='iso8859-1', 
                value_for_none=u'-'):
    """
    Retorna uma resposta no formato xls. ``rows`` deve ser lista de listas cujos 
    valores serão convertidos com ``human_str``.
    """
    import xlwt

    if not isinstance(rows, list) or \
        (len(rows) and not isinstance(rows[0], list)):
        raise ValueError('``rows`` must be a list of lists')

    response = HttpResponse(mimetype="application/ms-excel")
    response['Content-Disposition'] = 'attachment; filename=%s.xls' % name.encode(encoding)
    wb = xlwt.Workbook(encoding=encoding)
    sheet = wb.add_sheet("planilha1")

    for row_idx, row in enumerate(rows):
        row = [human_str(i, encoding=encoding, blank=u'-') for i in row]

        for col_idx, col in enumerate(row):
            sheet.write(row_idx, col_idx, label=col)

    wb.save(response)

    return response

def get_tl():
    """
    Retorna threadlocals.
    """
    tl = None
    exec 'from djtools.middleware import threadlocals as tl'
    return tl

####################
### Autocomplete ###

def autocomplete_view(request, app_name, class_name):
    """
    Gereric autocomplete view
    =========================
    `request.GET` expected args: 'q', 'manager_name', 'force_generic_seacrh'
    """
    SEARCH_FUNCTION_NAME = 'buscar'
    cls = models.get_model(app_name, class_name)
    if cls is None:
        raise Exception(u'Invalid Class')
    if 'pk' in request.GET:
        # Retorna apenas a representação unicode do objeto. É utilizado na 
        # escolha do objeto via change_list do admin.
        return HttpResponse(unicode(cls.objects.get(pk=request.GET['pk'])))
    if 'force_generic_search' not in request.GET and \
            hasattr(cls, SEARCH_FUNCTION_NAME):
        args = dict(autocomplete=True)
        for key, value in request.GET.items():
            args[str(key)] = value
        return HttpResponse(cls.buscar(**args))
    else:
        if 'search_fields' in request.GET:
            search_fields = request.GET['search_fields'].split(',')
        else:
            search_fields = None
        args = dict(
            autocomplete_format = True,
            q                   = request.GET.get('q', ''),
            control             = request.GET.get('control', ''),
            manager_name        = request.GET.get('manager_name', None),
            label_value         = request.GET.get('label_value', None),
            qs_filter           = request.GET.get('qs_filter', None),
            search_fields       = search_fields,
        )
        return HttpResponse(generic_search(cls, **args))

def generic_search(cls, q, autocomplete_format=True, manager_name=None,
                   label_value=None, search_fields=None, qs_filter=None, 
                   split_q=True, control=None):
    """
    Busca genérica utilizada para AutocompleteWidget
    ------------------------------------------------
    q
    autocomplete_format
    manager_name
    label_value
    search_fields
    qs_filter
    split_q
    control
    """
    def get_queryset(cls, manager_name=None):
        return manager_name and getattr(cls, manager_name) or cls.objects
        
    def construct_search(field_name):
        return '%s__icontains' % field_name
    
    def get_search_fields(cls):
        search_fields = []
        for f in cls._meta.fields:
            if f.__class__.__name__ == 'SearchField':
                return [f.name]
            if f.get_internal_type() in ['CharField', 'TextField']:
                search_fields.append(f.name)
        if not search_fields:
            raise Exception(u'Class %s don\'t have CharField or TextField.' \
                % cls.__name__)
        return search_fields
    search_fields = search_fields or get_search_fields(cls)

    qs = get_queryset(cls, None).all()
    
    if control:
        qs.query = loads_qs_query(control)
    
    words = split_q and q.split(' ') or [q]
    for word in words:
        or_queries = [models.Q(**{construct_search(str(field_name)): word}) \
                      for field_name in search_fields]
        qs = qs.filter(reduce(or_, or_queries))
    
    if qs_filter:
        k, v = qs_filter.split('=')
        if k.endswith('__in'):
            v = v.split(',')
        qs = qs.filter(**{str(k): v})
        
    if autocomplete_format:
        out = []
        for obj in qs[:20]: # Limitar a 20
            row = []
            if hasattr(obj, 'get_ext_combo_template'):
                row.append(obj.get_ext_combo_template().replace('|', '/').replace('\n',' '))
            row.append(eval_attr(obj, label_value or '__unicode__').replace('|', '/').replace('\n',' '))
            row.append(unicode(obj.pk))
            out.append(u'|'.join(row))
        return u'\n'.join(out)
    else:
        return qs

### Autocomplete ###
####################

def cache_queryset(queryset, keys, value=None):
    """
    Faz cache da queryset para evitar consultas repetitivas.
    ``keys`` refere-se a como os objetos serão organizados em cache;  o tamanho 
    limite de ``keys`` é 2.
    ``value`` refere-se ao valor (atributo) de cada chave da cache; caso seja None, 
    o valor será o próprio objeto.
    """
    if isinstance(keys, basestring):
        keys = [keys]
    if len(keys) > 2:
        raise ValueError('``keys`` size limit is 2.')
    
    cache = dict()
    
    if len(keys) == 1:
        key = keys[0]
        for obj in queryset:
            key_val = str(getattr(obj, key))
            cache[key_val] = value and getattr(obj, value) or obj
    
    elif len(keys) == 2:
        key1, key2 = keys
        for obj in queryset:
            key_val1 = str(getattr(obj, key1))
            if key_val1 not in cache:
                cache[key_val1] = dict()
            key_val2 = str(getattr(obj, key2))
            cache[key_val1][key_val2] = value and getattr(obj, value) or obj
    
    return cache
    

def user_has_one_of_perms(user, perms):
    for perm in perms:
        if user.has_perm(perm):
            return True
    return False

def get_search_field(model_class):
    for f in model_class._meta.fields:
        if f.__class__.__name__ == 'SearchField':
            return f

def to_ascii(txt, codif='utf-8'):
    if not isinstance(txt, basestring):
        txt = unicode(txt)
    if isinstance(txt, unicode):
        txt = txt.encode('utf-8')
    return normalize('NFKD', txt.decode(codif)).encode('ASCII', 'ignore')

def get_app_name(function):
    """Receives a function and returns the app name"""
    function_path = function.__module__.split('.')
    if len(function_path) == 2: # function is on the project
        return function_path[0]
    else: # function is on the app
        return function_path[1]

def get_template_path(function):
    """Returns the default template based on function"""
    app_name = get_app_name(function)
    if app_name == settings.PROJECT_NAME:
        return 'templates/%s.html' %(function.__name__)
    else:
        return '%s/templates/%s.html' %(app_name, function.__name__)

def rtr(template=None):
    """
    Deve ser usado como decorador de função.
    """
    def receive_function(function):
        def receive_function_args(request, *args, **kwargs):
            f_return = function(request, *args, **kwargs)
            if isinstance(f_return, HttpResponse):
                return f_return
            return render(template or get_template_path(function), f_return)
        return receive_function_args
    return receive_function

def breadcrumbs_add(request, ctx):
    bc = request.session.get('bc', SortedDict())
    title = ctx.get('title', '')
    if not title: # Não tem title definido, tenta montar baseado na URL
        path_splited = request.path.split('/')
        path_splited.reverse()
        for i in path_splited:
            if i and not i.isdigit():
                title = i.replace('_', ' ').capitalize()
                break
    if request.path == '/':
        bc = SortedDict()
    if title in bc: # Removendo itens após o ``title`` encontrado
        title_index = bc.keyOrder.index(title) 
        for key in bc.keyOrder[title_index+1:]:
            bc.pop(key)
    bc[title] = request.get_full_path()
    request.session['bc'] = bc
    ctx['breadcrumbs'] = bc
    
def breadcrumbs_previous_url(request):
    if 'bc' in request.session: 
        bc = request.session['bc']
        if len(bc)>1:
            return bc.values()[-2]
        else:
            return bc.values()[-1]
    return request.path

def render(template_name, ctx=None):
    """
    É o substituto do ``render_to_response``, só que já inclui as informações
    do RequestContext no contexto.
    """
    DEFAULT_TEMPLATE = 'djtools/templates/default.html'
    request = get_tl().get_request()
    context_instance = RequestContext(request)
    ctx = ctx or dict()
    
    # Breadcrumbs
    breadcrumbs_add(request, ctx)
    
    # Renderizando
    try:
        return render_to_response(template_name, ctx, 
            context_instance=context_instance)
    except TemplateDoesNotExist:
        logging.debug('Template %s not found; rendering %s instead' \
                % (template_name, DEFAULT_TEMPLATE))
        return render_to_response(DEFAULT_TEMPLATE, ctx, 
            context_instance=context_instance)

def httprr(url, message='', tag='success'):
    """
    É um ``HttpResponseRedirect`` com a possibilidade de passar uma mensagem.
    """
    
    request = get_tl().get_request()

    if message:
        from django.contrib import messages
        if tag == 'success':
            messages.success(request, message)
        else:
            messages.error(request, message)
    
    if url=='..' and tag=='success' and 'popup' in request.GET:
        return HttpResponse('<script>TINY.box.hide();</script>')
    
    if url == '.':
        url = request.path
    elif url=='..':
        url = breadcrumbs_previous_url(request)

    return HttpResponseRedirect(url)

def not_permitted(template=None, title=None, msg=None):
    template = template or 'djtools/templates/default.html'
    title = title or u'Ação não permitida'
    msg = msg or u'A ação desejada não pode ser feita.'
    return render(template, dict(h1=title, content=msg))

def sync_groups_and_permissions(data):
    """
    Syncronize groups and permissions.
    Group is created if not exists. Permissions must already exists.
    
    ``data`` format:
    {'<group_name>': ['<ct_app_label>.<ct_model>.<p_codename>']}
    
    Example of ``data``:
    {'operators': [
        'blog.article.add_article', ''blog.article.change_article'],
     'admins': 
        ['blog.article.add_article', 'blog.article.change_article', 'blog.article.delete_article']
    }
    """
    def get_perm(p):
        """
        ``p`` format: '<ct_app_label>.<ct_model>.<p_codename>'
        """
        try:
            ct_app_label, ct_model, p_codename = p.split('.')
        except ValueError:
            raise ValueError(u'Value must be in format "<ct_app_label>.<ct_model>.<p_codename>". Got "%s"' % p)
        try:
            return Permission.objects.get(content_type__app_label = ct_app_label,
                                          content_type__model     = ct_model,
                                          codename                = p_codename)
        except Permission.DoesNotExist:
            raise Permission.DoesNotExist(u'Permission "%s" does not exist.' % p)
    
    for group_name, perms in data.items():
        group, created = Group.objects.get_or_create(name=group_name)
        if not created:
            group.permissions.clear()
        for p in perms:
            try:
                perm = get_perm(p)
                group.permissions.add(perm)
            except Permission.DoesNotExist, e:
                print e
            

def client_is_server(request=None):
    request = request or get_tl().get_request()
    ip = request.META['REMOTE_ADDR'].split(':')[0]
    return ip in ['localhost', '127.0.0.1']

def user_has_profile(user=None):
    user = user or get_tl().get_user()
    if user is None:
        raise ValueError('User is ``None``')
    try:
        user.get_profile()
        return True
    except:
        return False

def user_has_perm_or_without_request(perm, user=None):
    """
    Testa se o usuário tem a permissão caso haja um request no threadlocals.
    Caso não haja request, retornará ``True``.
    Útil para ser utilizado no modelo, onde não se tem o request e também quando
    se deseja que quando não haja usuário logado seja ``True`` (exemplo: chamar 
    função no shell do Django).
    """
    user = user or get_tl().get_user()
    if not user:
        return True
    return user.has_perm(perm)

def group_required(group, login_url=None):
    """Must be used as decorator."""
    def _in_group(user, group):
        # FIXME: duplicado com djtools_templatetags.in_group. está aqui
        #        por causa de problemas com import circular.
        if isinstance(group, basestring):
            group_list = [g.strip() for g in group.split(',')]
        elif isinstance(group, list):
            group_list = [g.strip() for g in group]
        return user.groups.filter(name__in=group_list).count()
    return user_passes_test(lambda u: _in_group(u, group), login_url=login_url)


def any_permission_required(*args):
    """
    A decorator which checks user has any of the given permissions.
    permission required can not be used in its place as that takes only a
    single permission.
    """
    def test_func(user):
        for perm in args:
            if user.has_perm(perm):
                return True
        return False
    return user_passes_test(test_func)
        
    
###############################
# django.contrib.auth helpers #
###############################

def get_add_permission_for_model(model):
    """This should be used as param of user.has_perm method."""
    return model._meta.app_label + '.' + model._meta.get_add_permission()

def get_change_permission_for_model(model):
    """This should be used as param of user.has_perm method."""
    return model._meta.app_label + '.' + model._meta.get_change_permission()

def get_delete_permission_for_model(model):
    """This should be used as param of user.has_perm method."""
    return model._meta.app_label + '.' + model._meta.get_delete_permission()

def has_add_permission(model, user=None):
    """Tests if ``user`` has add permission for ``model``"""
    user = user or get_tl().get_user()
    return user.has_perm(get_add_permission_for_model(model))

def has_view_permission(model, user=None):
    """
    Testa se o user tem a perm ``change_``.
    """
    user = user or get_tl().get_user()
    return user.has_perm(get_change_permission_for_model(model))

def has_change_permission(model=None, obj=None, user=None):
    """
    Caso o model tenha a permission edit_model, ela será tratada; caso contrário,
    será o ``change_``
    """
    user = user or get_tl().get_user()
    if model is None and obj:
        model = obj.__class__
    
    edit_perm_codename = '%s.edit_%s' % (model._meta.app_label, model.__name__.lower())
    def has_edit_permission(model, perm):
        for p in model._meta.permissions:
            if p[0] == perm:
                return True
        
    # Model has no `edit` permission
    if (obj is None) or \
       (not has_edit_permission(model, edit_perm_codename.split('.')[1])):
        return user.has_perm(get_change_permission_for_model(model))
    
    # Model has `edit` permission
    return user.has_perm(edit_perm_codename)

def has_delete_permission(model=None, obj=None, user=None):
    """
    Condições para que o ``user`` possa remover o ``obj``:
    - Ter permissão ``app.delete_model``
    - Se existir método ``obj.can_delete(user)``, ele deve ser True
    """
    user = user or get_tl().get_user()
    if model is None and obj:
        model = obj.__class__
    
    if not user.has_perm(get_delete_permission_for_model(model)):
        return False
    if hasattr(obj, 'can_delete'):
        return obj.can_delete(user=user)
    return True

def get_admin_model_url(model, sufix=None):
    """Returns admin list or add link to ``model_cls``."""
    assert sufix in [None, 'add']
    base_url = u'/admin/%(app)s/%(model)s/'
    if sufix:
        base_url += sufix + u'/'
    params = dict(app=model._meta.app_label, model=model._meta.module_name)
    return base_url % params

def get_admin_object_url(obj):
    """Returns admin edit link for ``obj``."""
    base_url = get_admin_model_url(obj.__class__)
    return base_url + str(obj.pk) + '/'

def get_djtools_delete_object_url(obj):
    """Returns djtools delete object url for ``obj``"""
    model_cls = obj.__class__
    args = (model_cls._meta.app_label,
            model_cls._meta.module_name,
            obj.pk)
    return '/djtools/delete_object/%s/%s/%d/' % args

################################################################################

def has_related_objects(obj):
    for rel_obj in obj._meta.get_all_related_objects():
        try:
            if obj.__getattribute__(rel_obj.get_accessor_name()).select_related().count():
                return True
        except ObjectDoesNotExist:
            return False
    return False

def replace_object_references(obj_from, obj_to):
    """
    Substitui as referências de obj_from para obj_to
    """
    # Campos FK
    for r in obj_from._meta.get_all_related_objects():
        for obj_related in getattr(obj_from, r.get_accessor_name()).all():
            r.model.objects.filter(pk=obj_related.pk).update(**{r.field.name: obj_to})
    # Campos M2M
    for r in obj_from._meta.get_all_related_many_to_many_objects():
        for obj_related in getattr(obj_from, r.get_accessor_name()).all():
            getattr(obj_related, r.field.name).remove(obj_from)
            getattr(obj_related, r.field.name).add(obj_to)

def form_to_fieldset(form, fieldsets):
    out = []
    if form.errors:
        out.append('<p class="errornote">Por favor, corrija os erros abaixo.</p><br/>')
    
    for fieldset in fieldsets:
        fieldset_label = fieldset[0]
        field_rows = fieldset[1]['fields']
    
        out.append('<fieldset><legend>%s</legend>' % (fieldset_label))
    
        for row in field_rows:
            
            label_area = None
            if isinstance(row, dict):
                label_area = row.keys()[0]
                row = row.values()[0]
            
            out.append('<div class="form-row">')
            
            if label_area:
                out.append('<div class="form-section">%s</div>' % label_area)
            
            for key in row:
                
                field = form.fields[key]
                value = form.data.get(key, form.initial.get(key, ''))
                
                if isinstance(field.widget, forms.HiddenInput):
                    out.append(field.widget.render(key, value, attrs={'id': key}))
                    continue
                
                label = '<label class="%s" for="%s">%s</label>' % \
                    (field.required and 'required' or '', key, field.label)
                
                input_ = field.widget.render(key, value, attrs={'id': key})
                out.append('<div class="field %s">' %(key != row[0] and 'not-first' or ''))
                
                # label
                out.append('<div class="label">')
                out.append(label)
                out.append('</div>')
                
                # input
                out.append('<div class="input">')
                
                if key in form.errors:
                    out.append('<div class="errorlist">')
                    for error in form.errors[key]:
                        out.append('<li>%s</li>' % unicode(error))
                    out.append('</div>')
                out.append(input_)
                out.append('<div class="help_text">')
                out.append(field.help_text)
                out.append('</div>')
                out.append('</div>') # div.input
                
                out.append('</div>')
            
            out.append('</div>') # div.form-row
            
        out.append('</fieldset>')
        
    return ''.join(out)

def set_initial_for_fields(FormClass, initials):
    for key, value in initials.items():
        FormClass.base_fields[key].initial = value

class OverwriteStorage(FileSystemStorage):
    
    def get_available_name(self, name):
        """
        Returns a filename that's free on the target storage system, and
        available for new content to be written to.
        """
        # If the filename already exists, remove it as if it was a true file system
        if self.exists(name):
            os.remove(self.path(name))
        return name

def get_field_by_name(form_or_model_class, field_name):
    for field in form_or_model_class._meta.fields:
        if field.name == field_name:
            return field

def get_model_object(app_label, model_name, object_pk):
    """Useful for avoid imports from another apps"""
    return models.get_model(app_label, model_name)._base_manager.get(pk=object_pk)

def get_profile_model():
    """Returns the profile model based on AUTH_PROFILE_MODULE"""
    if not getattr(settings, 'AUTH_PROFILE_MODULE', False):
        raise ValueError('settings.AUTH_PROFILE_MODULE does not exist')
    try:
        app_label, model_name = settings.AUTH_PROFILE_MODULE.split('.')
        return models.get_model(app_label, model_name)
    except:
        raise ValueError('settings.AUTH_PROFILE_MODULE is invalid')

def get_profile(username):
    """Returns the profile instance based on AUTH_PROFILE_MODULE setting."""
    ProfileModel = get_profile_model()
    try:
        return ProfileModel.objects.get(username=username)
    except ProfileModel.DoesNotExist:
        return None

def get_obj_values(obj):
    values = []
    for f in obj.__class__._meta.fields:
        if isinstance(f, AutoField):
            continue
        if hasattr(obj, 'get_' + f.name + '_display'):
            value = getattr(obj, 'get_' + f.name + '_display')()
        else:
            value = getattr(obj, f.name)
        verbose_name = f.verbose_name
        if verbose_name == verbose_name.lower():
            verbose_name = verbose_name.title()
        values.append([verbose_name, value])
    return values


####################
# Non-Django Utils
####################

def eval_attr(obj, attr):
    """
    eval_attr(<Person Túlio>, 'city.country.name') --> 'Brazil'
    """
    path = attr.split('.')
    current_val = obj
    for node in path:
        current_val = getattr(current_val, node)
        if callable(current_val):
            current_val = current_val.__call__()
    return current_val

def randomic(size=10, allowed_chars='abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789'):
    """Returns a randomic string."""
    return ''.join([choice(allowed_chars) for i in range(size)])

def get_duplicated_values(l):
    duplicated_values = dict()
    for i in set(l):
        qtd = l.count(i)
        if qtd > 1:
            duplicated_values[i] = qtd
    return duplicated_values 

def br_title(value, strip=True):
    value_list = []
    pattern = r'\b(d?[a|e|i|o]s?|por|com)\b'
    if strip:
        value = value.strip()
    for word in value.lower().split():
        if not re.match(pattern, word):
            word = word.title()
        value_list.append(word)
    return ' '.join(value_list)

def diff_dicts(old, new, include_orfan_keys=True, compare_as_string=False):
    """
    Returns a diff dict in format:
        {'modified_key': [u'old_value', u'new_value']}
    -----
    ``old``: old object or dict
    ``new``: new object or dict
    ``include_orfan_keys``: include keys that exists in old but doesn't exists in new
    ``compare_as_string``:  convert to string before comparing values
    """
    if not isinstance(old, dict):
        old = old.__dict__
    if not isinstance(new, dict):
        new = new.__dict__
    diff = dict()
    for key in old.keys():
        if (not include_orfan_keys) and (key not in new):
            continue
        val1, val2 = old[key], new[key]
        cmp1, cmp2 = val1, val2
        if compare_as_string:
            if not isinstance(val1, basestring):
                cmp1 = str(val1)
            if not isinstance(val2, basestring):
                cmp2 = str(val2)
        if cmp1 != cmp2:
            diff[key] = [val1, val2]
    return diff

def diff_dicts_as_text(old, new, include_orfan_keys=True, compare_as_string=True):
    diff = diff_dicts(old, new, include_orfan_keys, compare_as_string)
    out = []
    for key, value in diff.items():
        out.append(u'%(key)s: "%(old)s" -> "%(new)s"' \
            % dict(key=key, old=value[0], new=value[1]))
    return u'\n'.join(out)

def dict_from_keys_n_values(keys, values):
    assert len(keys) == len(values)
    data = dict()
    for i in range(len(keys)):
        data[keys[i]] = values[i]
    return data

def str_to_dateBR(value, force_4_digits_year=True):
    """
    '01/01/2000' -> date(2000, 1, 1)
    """
    date_list = value.split('/')
    if len(date_list) != 3:
        raise ValueError(u'Data inválida.')
    if force_4_digits_year and len(date_list[2]) != 4:
        raise ValueError(u'O ano deve ter 4 dígitos.')
    date_list = [int(i) for i in date_list]
    date_list.reverse()
    return date(*date_list)

def str_money_to_decimal(value):
    """
    '1.010,10' -> Decimal('1010.00')
    """
    value_float = float(value.replace('.', '').replace(',', '.'))
    return Decimal(str(value_float))

def split_thousands(value, sep='.'):
    """
    split_thousands('1000000000') -> '1.000.000.000'
    """
    if not isinstance(value, basestring):
        value = str(value)
    negativo = False 
    if '-' in value:
        value = value.replace('-','')
        negativo = True
    if len(value) <= 3:
        if negativo:
            return '- ' + value
        else:
            return value
    if negativo:
        return '- ' + split_thousands(value[:-3], sep) + sep + value[-3:]
    else:
        return split_thousands(value[:-3], sep) + sep + value[-3:]

def mask_money(value):
    """
    mask_money(1) -> '1,00'
    mask_money(1000) -> '1.000,00'
    mask_money(1000.99) -> '1.000,99'
    """
    value = str(value)
    if '.' in value:
        reais, centavos = value.split('.')
        if len(centavos)>2:
            centavos = centavos[0:2]
    else:
        reais = value
        centavos = '00'
    reais = split_thousands(reais)
    return reais + ',' + centavos

def cpf_valido(value):
    from djtools.formfields import BrCpfField
    cpf_field = BrCpfField()
    try:
        cpf_field.clean(value)
        return True
    except ValidationError:
        return False
    
def cnpj_valido(value):
    from djtools.formfields import BrCnpjField
    cnpj_field = BrCnpjField()
    try:
        cnpj_field.clean(value)
        return True
    except ValidationError:
        return False

def mask_cpf(value):
    """
    '00000000000' -> '000.000.000-00'
    """
    value = mask_numbers(value)
    if not len(value):
        return ''
    return value[:3] + '.' + value[3:6] + '.' + value[6:9] + '-' + value[9:11]

def mask_cnpj(value):
    """
    'XXXXXXXXXXXXXX' -> 'XX.XXX.XXX/XXXX-XX'
    """
    value = mask_numbers(value)
    return value[:2] + '.' + value[2:5] + '.' + value[5:8] + '/' + value[8:12] + \
        '-' + value[12:14]

def mask_cep(value):
    """
    '99999999' -> '99999-999'
    """
    value = mask_numbers(value)
    return value[:5] + '-' + value[5:]

def mask_numbers(value):
    """
    '012abc345def' -> '012345'
    """
    return re.sub('\D', '', str(value))

def mask_placa(value):
    """
    'AAA1111' -> 'AAA-1111'
    """
    value = str(value)
    return value[:3] + '-' + value[3:]

def mask_horas_cursos(value):
    """
    '1111' -> '111.1'
    """
    value = str(value)
    return value 


def mask_empenho(value):
    """
    '1234123456' -> '1234NE123456'
    """
    value = str(value)
    return value[:4] + 'NE' + value[4:]

def lists_to_csv(lists, as_response=False, filename='report.csv'):
    """
    lists: list of lists

    The reader is hard-coded to recognise either '\r' or '\n' as end-of-line, 
    and ignores lineterminator. This behavior may change in the future.
    """
    if as_response:
        target = HttpResponse(mimetype='text/csv')
        target['Content-Disposition'] = 'attachment; filename=%s' % filename
    else:
        target = open(filename, 'w')
    
    new_lists = []
    for row in lists:
        new_row = [smart_str(i).replace('\n', '').replace('\r', '') for i in row]
        new_lists.append(new_row)
    
    writer = csv.writer(target)
    writer.writerows(new_lists)
    if as_response:
        return target
    else:
        target.close()

def range_float(start, stop, step):
    """
    Provides a range for float values; builtin ``range`` only supports int values.
    ----------
    >>> range_float(0, 2.5, 0.5)
    >>> [0, 0.5, 1.0, 1.5, 2.0]
    """
    if step == 0:
        raise ValueError('Step must not be 0')
    if start < stop and step < 0:
        raise ValueError('Step must positive for start %s and step %s' % (start, stop))
    if start > stop and step > 0:
        raise ValueError('Step must negative for start %s and step %s' % (start, stop))
    l = [start]
    current = start + step
    while current < stop:
        l.append(current)
        current += step
    return l

def date2datetime(date_):
    return datetime(date_.year, date_.month, date_.day)

def strptime_or_default(string, format_, default=None):
    """ If datetime.datetime(string, format) raises a exception, returns a default value
    >>> strptime_or_default('20101011', '%Y%m%d')
    datetime.datetime(2010, 10, 11, 0, 0)
    >>> strptime_or_default('20101000', '%Y%m%d')
    """
    try:
        return datetime.strptime(string, format_)
    except:
        return default

def get_age(begin, end=None):
    # adapted from 
    # http://stackoverflow.com/questions/765797/python-timedelta-in-years
    def yearsago(years, from_date=None):
        if from_date is None:
            from_date = datetime.now()
        try:
            return from_date.replace(year=from_date.year - years)
        except:
            # Must be 2/29!
            assert from_date.month == 2 and from_date.day == 29 # can be removed
            return from_date.replace(month=2, day=28,
                                     year=from_date.year-years)
    
    if isinstance(begin, date):
        begin = date2datetime(begin)
    if end is None:
        end = datetime.now()
    num_years = int((end - begin).days / 365.25)
    if begin > yearsago(num_years, end):
        return num_years - 1
    else:
        return num_years

def format_telefone(ddd, numero):
    """
    Retorna o número de telefone formatado como (XX) XXXX-XXXX. 
    O traço ficará sempre antes dos 4 últimos.
    Espaços existentes antes ou depois do ddd ou numero são removidos.
    >>> format_telefone('84', '12345678')
    '(84) 1234-5678'
    >>> format_telefone('48', '1234567')
    '(48) 123-4567'
    >>> format_telefone('', '12345678')
    '(XX) 1234-5678'
    >>> format_telefone(' 84 ', '12345678')
    '(84) 1234-5678'
    >>> format_telefone(' 84 ', '  12345678 ')
    '(84) 1234-5678'
    """
    ddd = ddd.strip()
    if not ddd:
        ddd = 'XX'
    
    numero = numero.strip()
    return '(%s) %s-%s' % (ddd, numero[:len(numero)-4], numero[len(numero)-4:])

###########################################################################
# ReadOnlyForm (Adaptado de http://www.djangosnippets.org/snippets/1340/) #
###########################################################################

class SpanWidget(forms.Widget):
    """
    Renders a value wrapped in a <span> tag.

    Requires use of specific form support. (see ReadonlyForm 
    or ReadonlyModelForm)
    """

    def render(self, name, value, attrs=None):
        final_attrs = self.build_attrs(attrs, name=name)
        return mark_safe(u'<span%s >%s</span>' % (
            forms.util.flatatt(final_attrs), self.original_value))

    def value_from_datadict(self, data, files, name):
        return self.original_value

class SpanField(forms.Field):
    """
    A field which renders a value wrapped in a <span> tag.

    Requires use of specific form support. (see ReadonlyForm 
    or ReadonlyModelForm)
    """

    def __init__(self, *args, **kwargs):
        kwargs['widget'] = kwargs.get('widget', SpanWidget)
        super(SpanField, self).__init__(*args, **kwargs)

class Readonly(object):
    """
    Base class for ReadonlyForm and ReadonlyModelForm

    Use example:
        class MyForm(ReadonlyModelForm):
            _readonly = ('foo',)
    """
    def __init__(self, *args, **kwargs):
        super(Readonly, self).__init__(*args, **kwargs)
        readonly_fieldnames = getattr(self, '_readonly', None)
        if not readonly_fieldnames:
            return
        for name, field in self.fields.items():
            if name in readonly_fieldnames:
                field.widget = SpanWidget()
            elif not isinstance(field, SpanField):
                continue
            field.widget.original_value = unicode(getattr(self.instance, name))

class ReadonlyForm(Readonly, forms.Form):
    pass

class ReadonlyModelForm(Readonly, forms.ModelForm):
    pass


def deprecated(func):
    """This is a decorator which can be used to mark functions as deprecated. 
    It will result in a warning being emmitted when the function is used. 
    Copied from http://code.activestate.com/recipes/391367-deprecated/ """
    def newFunc(*args, **kwargs):
        warnings.warn("Call to deprecated function %s." % func.__name__, category=DeprecationWarning, stacklevel=2)
        return func(*args, **kwargs)
    newFunc.__name__ = func.__name__
    newFunc.__doc__ = func.__doc__
    newFunc.__dict__.update(func.__dict__)
    return newFunc

def get_hours_between_dates(d0, d1=None):
    """
    Returns hours (float) between two datetimes. Weekends are desconsidered.
    """
    d1 = d1 or datetime.now()
    hours = (d1 - d0).seconds / 3600.0
    while d0 < (d1 - timedelta(1)):
        if d0.weekday() not in (5, 6): # not in (sat, sun)
            hours += 24
        d0 = d0 + timedelta(1)
    return hours

def group_by(list_of_dicts, group_by_key, sub_group_by_key=None, blank_label=None,
    as_dict=False):
    """
    returns [dict(group='group1', items=part_of_list_of_dicts),]
    """
    if not list_of_dicts:
        return []
    
    if blank_label is None:
        blank_label = u'Nenhum'
    
    list_of_dicts = sorted(list_of_dicts, key=itemgetter(group_by_key))
    current_group = list_of_dicts[0].get(group_by_key, None) or blank_label
    grouped = [dict(group=current_group, items=[])]
    
    for item in list_of_dicts:
        value = item.get(group_by_key, None) or blank_label
        if value != current_group: # create a new group
            current_group = value
            grouped.append(dict(group=current_group, items=[item]))
        else: # an existing group
            grouped[-1]['items'].append(item)
    
    if sub_group_by_key:
        for g in grouped:
            g['subgroups'] = group_by(g['items'], sub_group_by_key)
    
    if as_dict:
        grouped_as_dict = dict()
        for g in grouped:
            subgroups_as_dict = dict()
            for s in g['subgroups']:
                subgroups_as_dict[s['group']] = s
            g['subgroups_as_dict'] = subgroups_as_dict
            grouped_as_dict[g['group']] = g
        return grouped_as_dict
        
    return grouped



class QuerySetChain(object):
    """
    Chains multiple subquerysets (possibly of different models) and behaves as
    one queryset.  Supports minimal methods needed for use with
    django.core.paginator.
    """

    def __init__(self, *subquerysets):
        self.querysets = subquerysets

    def count(self):
        """
        Performs a .count() for all subquerysets and returns the number of
        records as an integer.
        """
        return sum(qs.count() for qs in self.querysets)

    def _clone(self):
        "Returns a clone of this queryset chain"
        return self.__class__(*self.querysets)

    def _all(self):
        "Iterates records in all subquerysets"
        return chain(*self.querysets)

    def __getitem__(self, ndx):
        """
        Retrieves an item or slice from the chained set of results from all
        subquerysets.
        """
        if type(ndx) is slice:
            return list(islice(self._all(), ndx.start, ndx.stop, ndx.step or 1))
        else:
            return islice(self._all(), ndx, ndx+1).next()


def get_rss_links(url_file_stream_or_string):
    import feedparser, urllib2
    feed = feedparser.parse(urllib2.urlopen(url_file_stream_or_string, timeout=2))
    rss_links = []
    for entry in feed['entries'][:min(5,len(feed['entries']))]:
        title = entry['title'].encode('utf-8', 'xmlcharrefreplace')
        rss_links.append({'title':   title, 
                          'url':     str(entry['links'][0]['href']), 
                          'updated': datetime.strptime(entry['updated'], '%Y-%m-%dT%H:%M:%SZ')})
    return rss_links

def dumps_qs_query(query):
    return base64.b64encode(zlib.compress(cPickle.dumps(query)))[::-1]
    
def loads_qs_query(query):
    return cPickle.loads(zlib.decompress(base64.b64decode(query[::-1])))

