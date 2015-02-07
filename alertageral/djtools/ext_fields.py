# -*- coding: utf-8 -*-

"""
Componentes Ext JS

def get_ext_combo_description(self):
        return '''
        <table style="outline: 0px; margin: 0px;">
            <tr>
                <td style="border: 0px">
                    <span>%(nome)s</span><br/>
                    <span>%(setor)s</span><br/>
                    <span>%(cargo)s</span><br/>
                    <b>%(matricula)s</b>
                </td>
                <td style="border: 0px;" width="80px">
                    <center><img class="foto-miniatura" src="%(img_src)s" /></center>
                </td>
            </tr>
        </table>
        ''' % dict(nome=self.nome, matricula=self.matricula, cargo=self.cargo_emprego,
            setor=self.setor and self.setor.get_caminho_as_html() or 'Sem setor', 
            img_src=self.foto and self.foto.url_75x75 or '/media/img/default.jpg')
"""

from django import forms
from django.db import models
from django.forms.fields import EMPTY_VALUES
from django.http import HttpResponse
from django.utils import simplejson
from django.utils.safestring import mark_safe
from operator import or_

def autocomplete_view(request, app_name, class_name):
    cls = models.get_model(app_name, class_name)
    
    if 'pk' in request.GET:
        return HttpResponse(unicode(cls.objects.get(pk=request.GET['pk'])))
    
    if 'search_fields' in request.GET:
        search_fields = request.GET['search_fields'].split(',')
    else:
        search_fields = None
    
    args = dict(
        query         = request.GET.get('query', ''),
        start         = request.GET.get('start', 0),
        limit         = request.GET.get('limit', ''),
        manager_name  = request.GET.get('manager_name', None),
        qs_filter     = request.GET.get('qs_filter', None),
        search_fields = search_fields,
    )
    return HttpResponse(request.GET['callback'] + '(' + simplejson.dumps(generic_search(cls, **args)) + ')')


def generic_search(cls, query, start=None, limit=None, manager_name=None, 
                   search_fields=None, qs_filter=None, split_query=True):
    
    def get_queryset(cls, manager_name=None):
        if not manager_name:
            return cls.objects
        else:
            return getattr(cls, manager_name)
        
    def construct_search(field_name):
        return '%s__icontains' % field_name
    
    def get_search_fields(cls):
        if hasattr(cls, 'get_dt_search_fields'):
            return cls.get_dt_search_fields()
        search_fields = []
        for f in cls._meta.fields:
            if f.get_internal_type() in ['CharField', 'TextField']:
                search_fields.append(f.name)
        return search_fields
    search_fields = search_fields or get_search_fields(cls)
    
    qs = get_queryset(cls, manager_name)
    
    words = split_query and query.split(' ') or [query]
    for word in words:
        or_queries = [models.Q(**{construct_search(str(field_name)): word}) \
                      for field_name in search_fields]
        qs = qs.filter(reduce(or_, or_queries))
    
    if qs_filter:
        k, v = qs_filter.split('=')
        if k.endswith('__in'):
            v = v.split(',')
        qs = qs.filter(**{str(k): v})
    
    if start and limit:
        qs = qs[int(start):int(start)+int(limit)]
    
    items = []
    for obj in qs:
        if hasattr(obj, 'get_ext_combo_template'):
            description = obj.get_ext_combo_template()
        else:
            description = unicode(obj)
        item = dict(
            value       = unicode(obj.pk), 
            title       = unicode(obj).strip(), 
            description = description.strip())
        items.append(item)
    
    return dict(
        items = items,
        total = get_queryset(cls, manager_name).filter(reduce(or_, or_queries)).count(),
    )


class ExtBrDateWidget(forms.DateTimeInput):
    # http://dev.sencha.com/deploy/ext-4.0.2a/docs/#/api/Ext.form.field.Date
    def render(self, name, value, attrs=None):
        if hasattr(value, 'strftime'):
            value = value.strftime('%d/%m/%Y')
        out = u"""
        <div id="%(name)s_widget" style="float: left;"></div>
        <script>
            var %(name)s_widget = new Ext.form.DateField({
    			fieldLabel: '',
    			id: '%(name)s',
    			name: '%(name)s',
    			width: 110,
    			xtype: 'datefield',
    			altFormats: '',
    			autoFitErrors: false,
    			format: 'd/m/Y',
    			value: '%(value)s'
    		});
    		%(name)s_widget.render('%(name)s_widget');
        </script>
        """
        return mark_safe(out % locals())


class ExtBrDateField(forms.DateField):
    
    widget = ExtBrDateWidget
    
    def __init__(self, input_formats=None, *args, **kwargs):
        super(ExtBrDateField, self).__init__(*args, **kwargs)
        self.input_formats = input_formats or ('%d/%m/%Y',)
    
    def clean(self, value):
        value = super(ExtBrDateField, self).clean(value)
        if value in EMPTY_VALUES:
            return None
        else:
            if value.year < 1900:
                raise forms.ValidationError('Informe uma data válida!')
        return value

class ExtBrDateRangeWidget(forms.MultiWidget):

    def __init__(self, widgets=[ExtBrDateWidget, ExtBrDateWidget], attrs={}):
        super(ExtBrDateRangeWidget, self).__init__(widgets, attrs)

    def decompress(self, value):
        if not value:
            return ['', '']
        return value

    def render(self, name, value, attrs=None):
        # value is a list of values, each corresponding to a widget
        # in self.widgets.
        if not isinstance(value, list):
            value = self.decompress(value)
        output = []
        final_attrs = self.build_attrs(attrs)
        id_ = final_attrs.get('id', None)
        for i, widget in enumerate(self.widgets):
            try:
                widget_value = value[i]
            except IndexError:
                widget_value = None
            if id_:
                final_attrs = dict(final_attrs, id='%s_%s' % (id_, i)) 
            output.append(widget.render(name + '_%s' % i, widget_value, final_attrs))
            if i == 0:
                output.append(u'<div style="float: left; margin: 0px 12px 0px 4px">até</div>')
        return mark_safe(self.format_output(output))


class ExtBrDateRangeField(forms.MultiValueField):

    widget = ExtBrDateRangeWidget

    def __init__(self, fields=(ExtBrDateField, ExtBrDateField), *args, **kwargs):
        super(forms.MultiValueField, self).__init__(*args, **kwargs)
        # Set 'required' to False on the individual fields, because the
        # required validation will be handled by MultiValueField, not by those
        # individual fields.
        for f in fields:
            f.required = False
        self.fields = fields

    def clean(self, value):
        """
        Retorna [(data), (data+1 dia)], pois o formato facilita as pesquisas
        em banco de dados: .filter(date__gt=start_date, date__lt=end_date)
        """
        field = ExtBrDateField()
        try:
            start_date, end_date = [field.clean(v) for v in value]
        except Exception, e:
            print e
            raise forms.ValidationError(u'A faixa de datas está inválida.')
        if start_date > end_date:
            raise forms.ValidationError(u'A data final deve ser maior que a inicial.')
        return [start_date, end_date]


class ExtComboWidget(forms.TextInput):
    
    def __init__(self, attrs=None, search_fields=None, manager_name=None,
                 qs_filter=None):
        
        self.id = id(self)
        self.attrs = attrs and attrs.copy() or {}
        extra_params = dict()
        
        if search_fields:
            if not isinstance(search_fields, (tuple, list)):
                raise ValueError('`search_fields` deve ser lista ou tupla')
            extra_params['search_fields'] = u','.join(search_fields)
        
        if manager_name:
            if not isinstance(manager_name, basestring):
                raise ValueError('`manager_name` deve ser basestring')
            extra_params['manager_name'] = manager_name
        
        if qs_filter:
            if not isinstance(qs_filter, basestring):
                raise ValueError('`qs_filter` deve ser basestring')
            extra_params['qs_filter'] = qs_filter
        
        self.extra_params = simplejson.dumps(extra_params)
        super(ExtComboWidget, self).__init__(attrs=attrs)
    
    def render(self, name, value, attrs=None):
        if attrs!=None and 'readonly' in attrs and attrs['readonly']==True:
            readonly = 'true'
        else:
            readonly = 'false'
        extra_params = self.extra_params
        qs = self.choices.queryset
        url = '/djtools/autocomplete/%s/%s/' \
            % (qs.model._meta.app_label, qs.model.__name__.lower())
        if hasattr(value, 'strftime'):
            value = value.strftime('%d/%m/%Y')
        if value:
            try:
                display_value = unicode(qs.get(pk=value))
            except qs.model.DoesNotExist:
                display_value = u''
                value = u''
        else:
            display_value = u''
            value = u''
        out = u"""
        <div id="container_%(name)s" style="display: table-cell;">
            <input type="hidden" id="id_%(name)s" name="%(name)s" value="%(value)s" />
        </div>
        <script>
            Ext.define('ComboItem_%(name)s', {
                extend: 'Ext.data.Model',
                proxy: {
                    type: 'jsonp',
                    url : '%(url)s',
                    extraParams: %(extra_params)s,
                    reader: {type: 'json', root: 'items', totalProperty: 'total'}
                },
                fields: [
                    {name: 'pk', type: 'string'},
                    {name: 'title', type: 'string'},
                    {name: 'description', type: 'string'},
                ],
            });
            
            var ds_%(name)s = Ext.create('Ext.data.Store', {
                pageSize: 20,
                model: 'ComboItem_%(name)s',
                remoteFilter: true,
                remoteSort: true
            });
            
            var widget_%(name)s = new Ext.form.ComboBox({
                name: '%(name)s_display',
                displayField: 'title',
                hideLabel: true,
                readOnly: %(readonly)s,
                xtype: 'combo',
                store: ds_%(name)s,
                minChars: 3,
                width: 600,

                listConfig: {
                    loadingText: 'Procurando...',
                    emptyText: 'Nenhum resultado encontrado.',
                    getInnerTpl: function() {
                        ComboItem_%(name)s.proxy.extraParams['query'] = widget_%(name)s.getValue(); 
                        return '{description}';
                    }
                },
                pageSize: 20
            });
            
            widget_%(name)s.render('container_%(name)s');
            
            // Ao clicar na seta pra baixo (expand), retirar o valor do combobox
            // da query que vai para o servidor.
            widget_%(name)s.addListener('expand', handleExpandEvent);
            function handleExpandEvent(field, options) {
                ComboItem_%(name)s.proxy.extraParams['query'] = widget_%(name)s.getValue();
            }
            
            // Após selecionar item, setar no hidden field
            widget_%(name)s.addListener('select', handleSelectEvent);
            function handleSelectEvent(field, value, options) {
                jQuery('[name=%(name)s]').val(value[0]['raw']['value']);
            }
            
            // Quando o texto de busca é alterado, forçar ir para a página 1
            widget_%(name)s.addListener('change', handleChangeEvent);
            function handleChangeEvent(newValue, oldValue, options) {
                ds_%(name)s.currentPage = 1;
            }
            
            // Definindo o valor inicial do widget
            if ('%(display_value)s' != '') {
                jQuery('[name=%(name)s_display]').val('%(display_value)s');
            }
        </script>
        """
        return mark_safe(out % locals())
