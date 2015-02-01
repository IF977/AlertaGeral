# -*- coding: utf-8 -*-

from django.conf.urls.defaults import *
from django.contrib import admin
from django.contrib.admin.options import csrf_protect_m
from django.contrib.admin.util import unquote
from django.contrib.admin.views.main import ChangeList
from django.core.exceptions import SuspiciousOperation
from django.db import models, transaction
from django.http import HttpResponseRedirect, HttpResponse
from django.utils.http import urlencode
from django.utils.safestring import mark_safe
from djtools import utils
from djtools.formfields import DateTimeFieldPlus, DateFieldPlus
from djtools.formwidgets import RegionalDateTimeWidget, RegionalDateWidget
from djtools.templatetags.djtools_templatefilters import status
from djtools.templatetags.djtools_templatetags import edit_object_icon, \
    view_object_icon
from djtools.utils import eval_attr, get_field_by_name, get_search_field, \
    to_ascii, CsvResponse, XlsResponse
import operator
from django.contrib.admin.views.main import ChangeList, PAGE_VAR, TO_FIELD_VAR,\
    ALL_VAR, IS_POPUP_VAR, ERROR_FLAG, SEARCH_VAR, ORDER_TYPE_VAR, ORDER_VAR,\
    field_needs_distinct
from django.utils.encoding import force_unicode, smart_str

class ChangeListPlus(ChangeList):
    
    def get_query_string(self, new_params=None, remove=None):
        """
        Método redefinido para manter a URL após aplicar filtros do `list_filter`.
        """
        qs = super(ChangeListPlus, self).get_query_string(new_params = new_params,
                                                          remove     = remove)
        if getattr(self.model_admin, 'current_tab', None):
            qs += '&' + urlencode(dict(tab=self.model_admin.current_tab))
        return qs
    
    # def get_query_set(self, request):
        # # FIXME: o parâmetro `request` só existe no Django 1.5, após migrar deixar
        # # a assinatura: `def get_query_set(self, request)` e ajustar chamada 
        # # abaixo para super(ChangeListPlus, self).get_query_set(request).
        # """
        # Método redefinido para tratar campos SearchField. Converte cada valor 
        # para ASCII maiúsculo e usa cláusula `contains` (default seria `icontains`).
        # """
        # qs = super(ChangeListPlus, self).get_query_set(request)
        # if get_search_field(self.model):
            # # Remove os filtros usados por causa do parâmetro GET `q`
            # for i in self.query.split():
                # qs.query.where.children.pop()
            # orm_lookups = ['%s__contains' % (str(search_field))
                           # for search_field in self.search_fields]
            # # Adicionando os filtros no `qs`
            # for bit in self.query.split():
                # bit = unicode(to_ascii(bit.upper()))
                # or_queries = [models.Q(**{orm_lookup: bit})
                              # for orm_lookup in orm_lookups]
                # qs = qs.filter(reduce(operator.or_, or_queries))
        # return qs
    def get_query_set(self):
        """O mÃ©todo foi sobrescrito para nÃ£o usar icontains em campos SearchField"""
        use_distinct = False

        qs = self.root_query_set
        lookup_params = self.params.copy() # a dictionary of the query string
        for i in (ALL_VAR, ORDER_VAR, ORDER_TYPE_VAR, SEARCH_VAR, IS_POPUP_VAR, TO_FIELD_VAR):
            if i in lookup_params:
                del lookup_params[i]
        for key, value in lookup_params.items():
            if not isinstance(key, str):
                # 'key' will be used as a keyword argument later, so Python
                # requires it to be a string.
                del lookup_params[key]
                lookup_params[smart_str(key)] = value

            if not use_distinct:
                # Check if it's a relationship that might return more than one
                # instance
                field_name = key.split('__', 1)[0]
                try:
                    f = self.lookup_opts.get_field_by_name(field_name)[0]
                except models.FieldDoesNotExist:
                    raise IncorrectLookupParameters
                use_distinct = field_needs_distinct(f)

            # if key ends with __in, split parameter into separate values
            if key.endswith('__in'):
                value = value.split(',')
                lookup_params[key] = value

            # if key ends with __isnull, special case '' and false
            if key.endswith('__isnull'):
                if value.lower() in ('', 'false'):
                    value = False
                else:
                    value = True
                lookup_params[key] = value

            if not self.model_admin.lookup_allowed(key, value):
                raise SuspiciousOperation(
                    "Filtering by %s not allowed" % key
                )

        # Apply lookup parameters from the query string.
        try:
            qs = qs.filter(**lookup_params)
        # Naked except! Because we don't have any other way of validating "params".
        # They might be invalid if the keyword arguments are incorrect, or if the
        # values are not in the correct type, so we might get FieldError, ValueError,
        # ValicationError, or ? from a custom field that raises yet something else
        # when handed impossible data.
        except:
            raise IncorrectLookupParameters

        # Use select_related() if one of the list_display options is a field
        # with a relationship and the provided queryset doesn't already have
        # select_related defined.
        if not qs.query.select_related:
            if self.list_select_related:
                qs = qs.select_related()
            else:
                for field_name in self.list_display:
                    try:
                        f = self.lookup_opts.get_field(field_name)
                    except models.FieldDoesNotExist:
                        pass
                    else:
                        if isinstance(f.rel, models.ManyToOneRel):
                            qs = qs.select_related()
                            break

        # Set ordering.
        if self.order_field:
            qs = qs.order_by('%s%s' % ((self.order_type == 'desc' and '-' or ''), self.order_field))

        # //MOD\\
        has_search_field = get_search_field(self.model)
        # //ENDMOD\\

        # Apply keyword searches.
        def construct_search(field_name):
            
            # //MOD\\ se for SearchField evitar o icontains por causa do desempenho
            if has_search_field:
                return "%s__contains" % field_name
            # //ENDMOD\\
            
            if field_name.startswith('^'):
                return "%s__istartswith" % field_name[1:]
            elif field_name.startswith('='):
                return "%s__iexact" % field_name[1:]
            elif field_name.startswith('@'):
                return "%s__search" % field_name[1:]
            else:
                return "%s__icontains" % field_name

        if self.search_fields and self.query:
            orm_lookups = [construct_search(str(search_field))
                           for search_field in self.search_fields]
            for bit in self.query.split():
                
                # //MOD\\ convertendo valor para ascii e upper para combinar com valor do SearchField
                if has_search_field and orm_lookups and orm_lookups[0].endswith('contains'):
                    bit = unicode(to_ascii(bit.upper()))
                # //ENDMOD\\
                
                or_queries = [models.Q(**{orm_lookup: bit})
                              for orm_lookup in orm_lookups]
                qs = qs.filter(reduce(operator.or_, or_queries))
            if not use_distinct:
                for search_spec in orm_lookups:
                    field_name = search_spec.split('__', 1)[0]
                    f = self.lookup_opts.get_field_by_name(field_name)[0]
                    if field_needs_distinct(f):
                        use_distinct = True
                        break

        if use_distinct:
            return qs.distinct()
        else:
            return qs

class ModelAdminPlus(admin.ModelAdmin):
    
    """
    O ModelAdminPlus foi criado para dar mais funcionalidades ao ModelAdmin.
    
    Atributos:
    ==========
    - list_display_icons = False
        O link para edição de cada objeto fica sendo um ícone (ao invés de ser o primeiro atributo do list_display)
    
    Métodos:
    ========
    
    get_action_bar(self, request)
    -----------------------------
    
    get_tabs(self, request)
    -----------------------
    Deve retornar uma lista de strings. Cada string deve corresponder ao nome de um método do ModelAdmin. 
    Se get_tabs retornar ``['foo']`` o método ``foo(self, request)`` deve ser implementado.
    
    export_to_csv(self, request, queryset)
    --------------------------------------
    Deve retornar uma lista de listas. Esse resultado será retornado como um CsvResponse.
    """
    
    # Atributos redefinidos
    change_list_template = 'djtools/templates/adminutils/change_list.html'
    change_form_template = 'djtools/templates/adminutils/change_form.html'
    
    # Atributos exclusivos ModelAdminPlus
    list_display_icons               = False
    
    formfield_overrides = {
        models.DateTimeField: {
            'form_class': DateTimeFieldPlus,
            'widget': RegionalDateTimeWidget},
        models.DateField: {
            'form_class': DateFieldPlus,
            'widget': RegionalDateWidget},
    }
    
    def show_status(self, obj):
        return mark_safe(status(obj.get_status_display()))
    show_status.admin_order_field = 'status'
    show_status.allow_tags = True
    show_status.short_description = u'Status'
    
    def show_list_display_icons(self, obj):
        out = [u'<ul class="list-display-icons">']
        for icon_html in [view_object_icon(obj), edit_object_icon(obj)]:
            if icon_html:
                out.append(u'<li>%s</li>' % icon_html)
        out.append(u'</ul>')
        return u''.join(out)
    show_list_display_icons.allow_tags = True
    show_list_display_icons.short_description = u'#'
    
    def __init__(self, *args, **kwargs):
        super(ModelAdminPlus, self).__init__(*args, **kwargs)
        self.list_display = tuple(self.list_display)
        if not self.search_fields and get_search_field(self.model):
            self.search_fields = (get_search_field(self.model).name,)
        if self.list_display_icons:
            self.list_display = ('show_list_display_icons',) + self.list_display
            self.list_display_links = ('show_list_display_icons',)
        # Remover qdo migrar para DJango 1.5 - CAST assegurar compatibilidade
        self.list_display = list(self.list_display)
    
    def get_changelist(self, request, **kwargs):
        return ChangeListPlus
    
    def get_actions(self, request):
        return []
    
    def get_tabs(self, request):
        """
        Retorna as abas visíveis para o usuário.
        """
        return []
    
    def get_view_inlines(self, request):
        return []
    
    def queryset(self, request):
        request.GET._mutable = True
        tab = request.GET.pop('tab', [None])[0]
        request.GET._mutable = False
        if tab:
            if tab not in self.get_tabs(request):
                raise SuspiciousOperation('Tab `%s` is unavailable.' % tab)
            return getattr(self, tab)(request)
        else:
            return super(ModelAdminPlus, self).queryset(request)
    
    def get_current_queryset(self, request):
        """
        Retorna o queryset exibido atualmente no changelist e é utilizado na
        ação ``export_to_csv``.
        """
        ChangeList = self.get_changelist(request)
        cl = ChangeList(request, self.model, self.list_display, self.list_display_links,
            self.list_filter, self.date_hierarchy, self.search_fields,
            self.list_select_related, self.list_per_page, self.list_max_show_all, self.list_editable, self)
        return cl.get_query_set(request)
    
    def has_change_permission(self, request, obj=None):
        return utils.has_change_permission(model=self.model, obj=obj, user=request.user)
    
    def has_delete_permission(self, request, obj=None):
        return utils.has_delete_permission(model=self.model, obj=obj, user=request.user)
    
    def get_action_bar(self, request):
        items = []
        
        # Botão para adicionar
        if self.has_add_permission(request):
            items.append(dict(url       = 'add/', 
                              label     = u'Adicionar %s' % self.model._meta.verbose_name,
                              css_class = 'success'))
        
        # Botão para exportar para CSV
        if hasattr(self, 'export_to_csv'):
            url = request.get_full_path()
            if '?' not in url: url = url + '?'
            if not url.endswith('?'): url = url + '&'
            url = url + 'export_to_csv=1' 
            items.append(dict(url   = url, 
                              label = u'Exportar para CSV'))
        
        if hasattr(self, 'export_to_xls'):
            url = request.get_full_path()
            if '?' not in url: url = url + '?'
            if not url.endswith('?'): url = url + '&'
            url = url + 'export_to_xls=1' 
            items.append(dict(url   = url, 
                              label = u'Exportar para XLS'))
        return items
    
    @csrf_protect_m
    def changelist_view(self, request, extra_context=None):
        
        self.change_list_template = 'djtools/templates/adminutils/change_list.html'
        self.current_tab = ''
        
        tabs_list = self.get_tabs(request)
        tabs = []
        if tabs_list:
            tabs.append(dict(label=u'Qualquer', lookup='', active=True))
        for tab in tabs_list:
            param, value = 'tab', tab
            is_active = request.GET.get(param) == value
            if is_active:
                tabs[0]['active'] = False
                self.current_tab = tab
            tabs.append(dict(label  = getattr(getattr(self, tab), 'short_description', tab), 
                             lookup = param + '=' + tab, 
                             active = is_active))
        
        # Chama a função de exportar para CSV
        if 'export_to_csv' in request.GET:
            request.GET._mutable = True
            del request.GET['export_to_csv']
            return CsvResponse(
                self.export_to_csv(request, queryset=self.get_current_queryset(request))
            )
        
        # XLS
        if 'export_to_xls' in request.GET:
            request.GET._mutable = True
            del request.GET['export_to_xls']

            return XlsResponse(
                self.export_to_xls(request, queryset=self.get_current_queryset(request))
            )
        
        extra_context = dict(
            object_tools_items        = self.get_action_bar(request),
            title                     = self.model._meta.verbose_name_plural.capitalize(),
            action_form               = False, ###
            tabs                      = tabs,
        )
        utils.breadcrumbs_add(request, extra_context)
        return super(ModelAdminPlus, self).changelist_view(request, extra_context)
    # def changelist_view(self, request, extra_context=None):
        
        # self.current_tab = ''
        
        # self.change_list_template = 'djtools/templates/adminutils/change_list.html'
        
        # filter_related_plus_specs = []
        # if hasattr(self, 'list_filter_plus'):
            # for title, lookup in self.list_filter_plus:
                # filter_spec = RelatedPlusFilterSpec(lookup, request, dict(), self.model, self, lookup_title=title)
                # filter_related_plus_specs.append(filter_spec)
        
        # tabs_list = self.get_tabs(request)
        # tabs = []
        # if tabs_list:
            # tabs.append(dict(label=u'Qualquer', lookup='', active=True))
        # for tab in tabs_list:
            # param, value = 'tab', tab
            # is_active = request.GET.get(param) == value
            # if is_active:
                # tabs[0]['active'] = False
                # self.current_tab = tab
            # tabs.append(dict(label  = getattr(getattr(self, tab), 'short_description', tab), 
                             # lookup = param + '=' + tab, 
                             # active = is_active))
        
        # # Chama a funÃ§Ã£o de exportar para CSV
        # if 'export_to_csv' in request.GET:
            # request.GET._mutable = True
            # del request.GET['export_to_csv']
            # return CsvResponse(
                # self.export_to_csv(request, queryset=self.get_current_queryset(request))
            # )
        
        # # XLS
        # if 'export_to_xls' in request.GET:
            # request.GET._mutable = True
            # del request.GET['export_to_xls']
            # return XlsResponse(
                # self.export_to_xls(request, queryset=self.get_current_queryset(request))
            # )
        
        # extra_context = dict(
            # filter_related_plus_specs = filter_related_plus_specs,
            # object_tools_items        = self.get_action_bar(request),
            # title                     = self.model._meta.verbose_name_plural.capitalize(),
            # action_form               = False, ###
            # tabs                      = tabs,
        # )
        # utils.breadcrumbs_add(request, extra_context)
        # return super(ModelAdminPlus, self).changelist_view(request, extra_context)    
    @csrf_protect_m
    @transaction.commit_on_success
    def add_view(self, request, form_url='', extra_context=None):
        extra_context = dict(
            title = u'Adicionar %s' % self.model._meta.verbose_name,
        )
        utils.breadcrumbs_add(request, extra_context)
        return super(ModelAdminPlus, self).add_view(request, form_url, extra_context)
    
    @csrf_protect_m
    @transaction.commit_on_success
    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = dict(
            title = u'Editar %s' % unicode(self.get_object(request, unquote(object_id))),
        )
        utils.breadcrumbs_add(request, extra_context)
        return super(ModelAdminPlus, self).change_view(self, request, object_id, form_url, extra_context)
    
    @csrf_protect_m
    @transaction.commit_on_success
    def delete_view(self, request, object_id, extra_context=None):
        extra_context = dict(
            title = u'Remover %s' % self.model._meta.verbose_name,
        )
        utils.breadcrumbs_add(request, extra_context)
        return super(ModelAdminPlus, self).delete_view(request, object_id, extra_context)
    
    def response_change(self, request, obj):
        if "_continue" in request.POST or "_addanother" in request.POST:
            return super(ModelAdminPlus, self).response_change(request, obj)
        elif "tinybox" in request.GET or "_popup" in request.POST:
            return HttpResponse('<script>TINY.box.hide();</script>')
        else:
            self.message_user(request, u'Atualização realizada com sucesso.')
            return HttpResponseRedirect(utils.breadcrumbs_previous_url(request))
    
    def response_add(self, request, obj, post_url_continue=None):
        if "_continue" in request.POST or "_addanother" in request.POST:
            return super(ModelAdminPlus, self).response_change(request, obj)
        elif "tinybox" in request.GET or "_popup" in request.POST:
            return HttpResponse('<script>TINY.box.hide();</script>')
        else:
            self.message_user(request, u'Cadastro realizado com sucesso.')
            return HttpResponseRedirect(utils.breadcrumbs_previous_url(request))
    
    def get_urls(self):
        new_urls = patterns('',
            (r'^(.+)/view/$', self.render_view_object),
        )
        return new_urls + super(ModelAdminPlus, self).get_urls()
    
    def get_view_obj_items(self, obj):
        
        def _get_fieldsets(self):
            if self.fieldsets:
                return self.fieldsets
            else:
                fields = [f.name for f in obj.__class__._meta.fields if f.name != 'id']
                return ((u'', {'fields': (fields,)}),)
        
        fieldsets = _get_fieldsets(self)
        max_fields_by_row = 1
        for fieldset_name, fieldset_dict in fieldsets:
            for item in fieldset_dict['fields']:
                if isinstance(item, basestring): continue
                if len(item) > max_fields_by_row: max_fields_by_row = len(item)
         
        items = []
        for fieldset_name, fieldset_dict in fieldsets:
            item_dict = dict(fieldset=fieldset_name, rows=[])
            for fieldset_fields_item in fieldset_dict['fields']:
                if isinstance(fieldset_fields_item, basestring):
                    fieldset_fields_item = [fieldset_fields_item]
                fields = []
                for field_name in fieldset_fields_item:
                    last_field_in_row = field_name == fieldset_fields_item[-1]
                    if last_field_in_row:
                        colspan = (max_fields_by_row - len(fieldset_fields_item)) * 2 + 1
                    else: 
                        colspan = 1
                    model_field = get_field_by_name(self.model, field_name)
                    field_dict = dict(label   = model_field.verbose_name,
                                      value   = getattr(obj, field_name),
                                      colspan = colspan)
                    fields.append(field_dict)
                item_dict['rows'].append(fields)
            items.append(item_dict)
        return items
    
    def render_view_object(self, request, obj_pk):
        
        obj = self.model.objects.get(pk=int(obj_pk))
        title = unicode(obj)
        obj_items = self.get_view_obj_items(obj)
        
        inlines = dict()
        for func_name in self.get_view_inlines(request):
            func = getattr(self, func_name)
            columns = getattr(func, 'columns', ['__unicode__'])
            inline_items = []
            objects = func(obj)
            if not objects:
                continue
            for model_obj in objects:
                model_cls = model_obj.__class__
                values = []
                for col in columns:
                    values.append(eval_attr(model_obj, col))
                inline_items.append(values)
            
            columns_verbose_names = []
            for col in columns:
                if col == '__unicode__': verbose_name = model_cls._meta.verbose_name
                else: verbose_name = get_field_by_name(model_cls, col).verbose_name 
                columns_verbose_names.append(verbose_name)
            
            inlines[getattr(func, 'short_description', func_name)] = dict(
                columns=columns_verbose_names, 
                items=inline_items)
        
        return utils.render('djtools/templates/adminutils/render_view_object.html', locals())
    
