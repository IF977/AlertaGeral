# -*- coding: utf-8 -*-

from decimal import Decimal
from django.conf import settings
from django.forms.util import flatatt
from django.forms.widgets import SelectMultiple, CheckboxInput, Widget,\
    TextInput, DateTimeInput, TimeInput, MultiWidget, Select
from django.template.loader import render_to_string
from django.utils import simplejson
from django.utils.datastructures import MultiValueDict
# from django.utils.encoding import force_unicode,force_text
from django.utils.encoding import force_unicode
# from django.utils.html import escape, conditional_escape, format_html
from django.utils.html import escape, conditional_escape
from django.utils.safestring import mark_safe
from djtools.utils import randomic, has_change_permission, has_add_permission, \
    mask_cpf, mask_money, mask_placa, mask_cnpj, mask_empenho, mask_horas_cursos, \
    dumps_qs_query
from sre_parse import isdigit
import itertools

# TODO: gerar id's para os widgets (funcionar com label for)
# TODO: pegar max_length do models
# TODO: melhorar visualizacao do field required

class Masked:
    class Media:
        js = (
            '/static/djtools/jquery/jquery.maskedinput.js',
            '/static/djtools/jquery/widgets-core.js',
        )

class MaskedInput(TextInput, Masked):
    pass

class BrDataWidget(DateTimeInput, Masked):
    """
    Define o ``format`` e aplica a máscara javascript a partir da classe.
    """
    format = '%d/%m/%Y'
    
    def __init__(self, attrs=None, format=None, show_label=True):
        attrs = attrs or {}
        if show_label:
            attrs.update({'class': 'br-data-widget', 'size': '10', 'maxlength': '10'})
        else:
            attrs.update({'class': 'br-data-widget labeless', 'size': '10', 'maxlength': '10'})
        super(DateTimeInput, self).__init__(attrs)
        if format:
            self.format = format


class TimeWidget(TimeInput, Masked):
    """
    Aplica a máscara javascript a partir da classe.
    """
    def __init__(self, attrs=None, format=None):
        attrs = attrs or {}
        attrs.update({'class': 'time-widget', 'size': '8', 'maxlength': '8'})
        super(TimeInput, self).__init__(attrs)
        if format:
            self.format = format

class RegionalDateWidget(DateTimeInput, Masked):
    
    def render(self, name, value, attrs=None):
        value = self._format_value(value)
        if value:
            value = value.replace(' 00:00', '')
        attrs = attrs or {}
        attrs.update({'class': 'br-data-widget'})
        id_ = 'id_%s' % name
        language, country = settings.LANGUAGE_CODE.split('-')    
        script = u"""
        <script>
            $(function() {
                $("#%s").datepicker();
                $("#%s").datepicker( "option", "dateFormat", '%s');
                $("#datepicker").datepicker("option", $.datepicker.regional['%s-%s']);
            });
        </script>""" % (id_, id_, 'dd/mm/yy', language, country.upper())
        html = super(RegionalDateWidget, self).render(name, value, attrs)
        return mark_safe('%s%s' % (html, script))

class RegionalDateTimeWidget(DateTimeInput, Masked):
    
    def value_from_datadict(self, data, files, name):
        """Concatena os valores dos inputs para data e hora."""
        time_value = data.get('%s_time' % name, u'00:00')
        value = super(RegionalDateTimeWidget, self).value_from_datadict(data, files, name)
        if value:
            if len(time_value) == 5: # Não tem os segundos
                time_value = '%s:00' % time_value
            return u'%s %s' % (value, time_value)
        return u''
    
    def render(self, name, value, attrs=None):
        value = self._format_value(value)
        attrs = attrs or {}
        attrs.update({'class': 'br-data-widget'})
        if value:
            date_value, time_value = value.split()
        else:
            date_value, time_value = u'', u'00:00'
        id_ = 'id_%s' % name
        language, country = settings.LANGUAGE_CODE.split('-')    
        script = u"""
        <script>
            $(function() {
                $("#%s").datepicker();
                $("#%s").datepicker("option", "dateFormat", '%s');
                $("#datepicker").datepicker("option", $.datepicker.regional['%s-%s']);
            });
        </script>""" % (id_, id_, 'dd/mm/yy', language, country.upper())
        html = super(RegionalDateTimeWidget, self).render(name, date_value, attrs)
        html += u''' <input style="width:55px;" type="text" class="short-time-widget" 
            id="%s_time" name="%s_time" value="%s"/>''' % (id, name, time_value)
        return mark_safe(u'%s%s' % (html, script))


class BrDataHoraWidget(DateTimeInput, Masked):
    """
    Define o ``format`` e aplica a máscara javascript a partir da classe.
    """
    format = '%d/%m/%Y %H:%M:%S'

    def __init__(self, attrs=None, format=None, show_label=True):
        attrs = attrs or {}
        if show_label:
            attrs.update({'class': 'br-datahora-widget', 'size': '19', 'maxlength': '19'})
        else:
            attrs.update({'class': 'br-datahora-widget labeless', 'size': '19', 'maxlength': '19'})
        super(DateTimeInput, self).__init__(attrs)
        if format:
            self.format = format


class BrTelefoneWidget(MaskedInput):
    
    def __init__(self, attrs={}):
        attrs.update({'class': 'br-phone-number-widget', 'size': '18', 'maxlength': '18'})
        super(BrTelefoneWidget, self).__init__(attrs=attrs)

class BRCpfCnpjWidget(MaskedInput):
    
    def __init__(self, attrs={}):
        attrs.update({'class': 'br-cpf-cnpj-widget', 'size': '18', 'maxlength': '18'})
        super(self.__class__, self).__init__(attrs=attrs)
    
    def render(self, name, value, attrs=None):
        return super(self.__class__, self).render(name, value, attrs=attrs)

class BRCpfWidget(MaskedInput):
    
    def __init__(self, attrs={}):
        attrs.update({'class': 'br-cpf-widget', 'size': '14', 'maxlength': '14'})
        super(self.__class__, self).__init__(attrs=attrs)
    
    def render(self, name, value, attrs=None):
        if value and value.isdigit() and len(value) == 11:
            value = mask_cpf(value)
        return super(self.__class__, self).render(name, value, attrs=attrs)


class BrCnpjWidget(MaskedInput):
    
    def __init__(self, attrs={}):
        attrs.update({'class': 'br-cnpj-widget', 'size': '18', 'maxlength': '18'})
        super(self.__class__, self).__init__(attrs=attrs)
    
    def render(self, name, value, attrs=None):
        if value and value.isdigit() and len(value) == 14:
            value = mask_cnpj(value)
        return super(self.__class__, self).render(name, value, attrs=attrs)

class BrDinheiroWidget(MaskedInput):

    def __init__(self, attrs={}):
        attrs.update({'class': 'br-dinheiro-widget', 'size': '15', 'maxlength': '15'})
        super(BrDinheiroWidget, self).__init__(attrs=attrs)
    
    def _format_value(self, value):
        if value is None:
            value = u''
        expected_types = (basestring, Decimal)
        if not isinstance(value, expected_types):
            raise ValueError('Value type must be in %s' % expected_types)
        if isinstance(value, basestring) and (value == u'' or ',' in value):
            # value is blank or already formatted
            return value
        else:
            return mask_money(value)
    
    def render(self, name, value, attrs=None):
        value = self._format_value(value)
        return super(BrDinheiroWidget, self).render(name, value, attrs=attrs)
    

class BRDateRangeWidget(MultiWidget):

    def __init__(self, widgets=[RegionalDateWidget, RegionalDateWidget], attrs={}):
        super(self.__class__, self).__init__(widgets, attrs)

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
                output.append(u'<span style="padding: 0px 10px 0px 4px">até</span>')
        return mark_safe(self.format_output(output))


class NumEmpenhoWidget(MaskedInput):
    
    def __init__(self, attrs={}):
        attrs.update({'class': 'empenho-widget', 'size': '14', 'maxlength': '12'})
        super(self.__class__, self).__init__(attrs=attrs)
    
    def render(self, name, value, attrs=None):
        if value and len(value) == 10:
            value = mask_empenho(value)
        return super(self.__class__, self).render(name, value, attrs=attrs)


class HorasCursosWidget(MaskedInput):
    
    def __init__(self, attrs={}):
        attrs.update({'class': 'horas-cursos-widget', 'size': '7', 'maxlength': '5'})
        super(self.__class__, self).__init__(attrs=attrs)
        
    def _format_value(self, value):
        if value is None:
            value = u''
        expected_types = (basestring, float)
        if not isinstance(value, expected_types):
            raise ValueError('Value type must be in %s' % expected_types)
        if isinstance(value, basestring) and (value == u'' or ('.' in value and len(filter(isdigit, value.split('.')))==2)):
            # value is blank or already formatted
            return value
        else:
            return mask_horas_cursos(value)
    
    def render(self, name, value, attrs=None):
        value = self._format_value(value)
        return super(HorasCursosWidget, self).render(name, value, attrs=attrs)


    

class BrPlacaVeicularWidget(MaskedInput):
    
    def __init__(self, attrs={}):
        attrs.update({'class': 'placa-widget', 'size': '10', 'maxlength': '8'})
        super(self.__class__, self).__init__(attrs=attrs)
    
    def render(self, name, value, attrs=None):
        if value and len(value) == 7:
            value = mask_placa(value)
        return super(self.__class__, self).render(name, value, attrs=attrs)
  
  
class BrCepWidget(MaskedInput):
    
    def __init__(self, attrs={}):
        attrs.update({'class': 'br-cep-widget', 'size': '9', 'maxlength': '9'})
        super(self.__class__, self).__init__(attrs=attrs)
    
    
class IntegerWidget(MaskedInput):
    
    def __init__(self, attrs={}):
        attrs.update({'class': 'integer-widget'})
        super(self.__class__, self).__init__(attrs=attrs)
    

class AlphaNumericWidget(MaskedInput):
    
    def __init__(self, attrs={}):
        attrs.update({'class': 'alpha-widget'})
        super(self.__class__, self).__init__(attrs=attrs)


class AlphaNumericUpperCaseWidget(MaskedInput):
    
    def __init__(self, attrs={}):
        attrs.update({'class': 'upper-text-widget'})
        super(self.__class__, self).__init__(attrs=attrs)


class CapitalizeTextWidget(MaskedInput):
    
    def __init__(self, attrs={}):
        attrs.update({'class': 'capitalize-text-widget'})
        super(self.__class__, self).__init__(attrs=attrs)

###############
# Autocomplete Configuration
###############

BASE_SEARCH_URL = 'autocompletar'
def get_search_url(cls):
    data = dict(base_search_url=BASE_SEARCH_URL, app_label=cls._meta.app_label,
                model_label=cls.__name__.lower())
    return '/%(base_search_url)s/%(app_label)s/%(model_label)s/' % data

def get_change_list_url(cls):
    data = dict(app_label=cls._meta.app_label, model_name=cls.__name__.lower())
    return '/admin/%(app_label)s/%(model_name)s/' % data

def get_add_another_url(cls):
    data = dict(app_label=cls._meta.app_label, model_name=cls.__name__.lower())
    return '/admin/%(app_label)s/%(model_name)s/add/' % data

ALL_AUTOCOMPLETE_OPTIONS = (
    'matchCase',
    'matchContains',
    'mustMatch',
    'minChars',
    'selectFirst',
    'extraParams',
    'formatItem',
    'formatMatch',
    'formatResult',
    'multiple',
    'multipleSeparator',
    'width',
    'autoFill',
    'max',
    'highlight',
    'scroll',
    'scrollHeight'
)

DEFAULT_AUTOCOMPLETE_OPTIONS = dict(autoFill=True, minChars=2, scroll=False, extraParams=dict())

def set_autocomplete_options(obj, options):
    options = options or dict()
    for option in options.keys():
        if option not in ALL_AUTOCOMPLETE_OPTIONS:
            raise ValueError(u'Autocomplete option error: "%s" not in %s' \
                % (option, ALL_AUTOCOMPLETE_OPTIONS))
    new_options = DEFAULT_AUTOCOMPLETE_OPTIONS.copy()
    new_options.update(options)
    obj.options = simplejson.dumps(new_options)


###############
# AutocompleteWidget 
# http://jannisleidel.com/2008/11/autocomplete-form-widget-foreignkey-model-fields/) 
###############

class AutocompleteWidget(TextInput):
    """
    Widget desenvolvido para ser utilizado com field ``forms.ModelChoiceField``.
    View Ajax default: djtools.utils.autocomplete_view
    """
    # TODO: mover scripts do template ``autocomplete_widget.html`` para arquivo js.
    class Media:
        js = (
            "/static/djtools/jquery/jquery.autocomplete.js",
            "/static/djtools/jquery/jquery.bgiframe.min.js",
            "/static/admin/js/admin/RelatedObjectLookups.js",
        )
        css = {'all': ("/static/djtools/jquery/jquery.autocomplete.css",)}
    
    def __init__(self, url=None, id_=None, attrs=None, show=True, help_text=None, 
                 readonly=False, side_html=None, label_value=None, 
                 search_fields=None, manager_name=None, qs_filter=None, **options):
        self.help_text = help_text
        self.show = show
        self.attrs = attrs and attrs.copy() or {}
        self.id_ = id_ or randomic()
        self.url = url
        self.readonly = readonly
        self.side_html = side_html
        
        options['extraParams'] = options.get('extraParams', {})
        if label_value:
            options['extraParams']['label_value'] = label_value
        if search_fields:
            if not isinstance(search_fields, (tuple, list)):
                raise ValueError('`search_fields` deve ser lista ou tupla')
            options['extraParams']['search_fields'] = u','.join(search_fields)
        if manager_name:
            if not isinstance(manager_name, basestring):
                raise ValueError('`manager_name` deve ser basestring')
            options['extraParams']['manager_name'] = manager_name
        if qs_filter:
            if not isinstance(qs_filter, basestring):
                raise ValueError('`qs_filter` deve ser basestring')
            options['extraParams']['qs_filter'] = qs_filter
        
        set_autocomplete_options(self, options)
        super(AutocompleteWidget, self).__init__(self.attrs)
    
    def render(self, name, value=None, attrs={}):
        model_cls = self.choices.queryset.model
        value = value or ''
        if not isinstance(value, (basestring, int, model_cls)):
            raise ValueError('value must be basestring, int or a models.Model instance. Got %s.' % value)
        if isinstance(value, model_cls):
            value = value.pk
        self.url = self.url or get_search_url(model_cls)
        context = dict(id                    = self.id_,
                       value                 = value,
                       options               = self.options,
                       name                  = name,
                       url                   = self.url,
                       change_list_url       = get_change_list_url(model_cls),
                       add_another_url       = get_add_another_url(model_cls),
                       # has_change_permission = has_change_permission(model_cls),
                       # has_add_permission    = has_add_permission(model_cls),
                       side_html             = self.side_html,
                       readonly              = self.readonly,
                       attrs                 = self.attrs,
                       show                  = self.show,
                       control               = dumps_qs_query(self.choices.queryset.none().query),
                       help_text             = self.help_text)
        output = render_to_string('djtools/templates/autocomplete_widget.html',
                                  context)
        return mark_safe(output)


class AjaxMultiSelect(Widget):
    class Media:
        js = (
            "/static/djtools/jquery/jquery.autocomplete.js",
            "/static/djtools/jquery/jquery.bgiframe.min.js",
        )
        css = {'all': ("/static/djtools/jquery/jquery.autocomplete.css",)}

    def __init__(self, auto_url=None, app_name=None, class_name=None, attrs=None,
                 **options):
        self.auto_url = auto_url
        set_autocomplete_options(self, options)
        super(self.__class__, self).__init__(attrs)

    def build_attrs(self, extra_attrs=None, **kwargs):
        ret = super(AjaxMultiSelect, self).build_attrs(extra_attrs=None, **kwargs)
        return ret

    def render(self, name, value, attrs=None, choices=()):
        self.auto_url = self.auto_url or get_search_url(self.choices.queryset.model)
        final_attrs = self.build_attrs(attrs)
        final_attrs.setdefault('id', 'id_' + name)
        if value:
            items = [self.choices.queryset.model.objects.get(pk=id_) for id_ in value]
        else:
            items = []
        context = dict(name=name,
                       attrs=flatatt(final_attrs),
                       url=self.auto_url,
                       options=self.options,
                       items=items)
        output = render_to_string('djtools/templates/multipleautocomplete_widget.html',
                                  context)
        return mark_safe(output)

    def value_from_datadict(self, data, files, name):
        if isinstance(data, MultiValueDict):
            return data.getlist(name)
        return data.get(name, None)


###############
# TreeWidget
###############

class ExtTreeWidget(TextInput):
    pass

class TreeWidget(TextInput):
    class Media:
        js = (
            "/static/djtools/jstree/_lib.js",
            "/static/djtools/jstree/tree_component.min.js",)
        css = {'all': ("/static/djtools/jstree/tree_component.css",
                       "/static/djtools/jstree/style.css",)}
    
    def __init__(self, id_=None, root_nodes=None, attrs={}):
        self.id_ = id_ or randomic()
        super(TreeWidget, self).__init__(attrs)
        self.root_nodes = root_nodes
    
    def get_parent_field(self):
        cls = self.choices.queryset.model
        for field in cls._meta.fields:
            if field.get_internal_type() == 'ForeignKey' and field.rel.to == cls:
                return field
        raise Exception(u'Class %s has no self relation' % (cls.__name__))

    def get_root_nodes(self):
        """ Returns a root nodes list
        But for while, this list has a only element. 
        This need to be fix. (ticket #1044)
        """
        args = {self.get_parent_field().name: None}
        return self.choices.queryset.filter(**args).order_by('id')[0:1]
    
    def get_children(self, node):
        args = {self.get_parent_field().name: node}
        return self.choices.queryset.filter(**args)

    def get_tree_as_ul(self, node):
        nodes = []
        nodes.append('<ul>')
        self.__get_descendents_helper(node, nodes)
        nodes.append('</ul>')
        return nodes
    
    def label_from_instance(self, obj):
        return unicode(obj)

    def __get_descendents_helper(self, node, nodes):
        nodes.append('<li id="%(pk)s"><a href="#" title="%(title)s">%(label)s</a>' \
            % dict(pk=node.pk, title=node.nome, label=self.label_from_instance(node)))
        node_children = self.get_children(node)
        if node_children:
            nodes.append('<ul>')
        for c in node_children:
            self.__get_descendents_helper(c, nodes)
        if node_children:
            nodes.append('</ul>')
        nodes.append('</li>')
        return nodes
    
    def render(self, name, value=None, attrs={}):
        # FIXME: deixar ``context`` mais flexível
        value = value or ''
        self.root_nodes = self.root_nodes or self.get_root_nodes()
        tree_as_ul = []
        for root_node in self.root_nodes:
            tree_as_ul += self.get_tree_as_ul(root_node)
        tree_as_ul = ''.join(tree_as_ul)
        output = u"""\
        <div class="tree-container" id="tree-%(name)s">
            %(tree_as_ul)s
        </div>
        <input type="hidden" name="%(name)s" value="%(value)s"/>
        <script type="text/javascript">
            root_nodes = $("#tree-%(name)s > ul");
            root_nodes.addClass("tree-ul-root");
            for (i=0; i<root_nodes.length; i++) {
                root_node = $(root_nodes[i]);
                root_node.attr("id", "root-node-"+(i+1));
            }
            $("#tree-%(name)s > ul").css("padding", "0");
            $("#tree-%(name)s > ul.tree-ul-root").tree({
                ui: {
                    theme_name: "default", 
                    theme_path: "/static/djtools/jstree/themes/",
                    context     : [ 
                        {
                            id      : "open-branch",
                            label   : "Open Branch", 
                            visible : function (NODE, TREE_OBJ) { return true }, 
                            action  : function (NODE, TREE_OBJ) { 
                                
                            } 
                        }
                    ]
                },
                callback: {
                    onselect: function(node, tree_obj) {
                        value = node.getAttribute("id")
                        $("input[name=%(name)s]").val(value)
                    },
                },
            });
            
            function select_node(node_id) {
                for (i=0; i<root_nodes.length; i++) {
                    root_node = $(root_nodes[i]);
                    $.tree_reference(root_node.attr("id")).select_branch($('#'+node_id));
                }
            }
        </script>""" % dict(
            name=name, value=value, tree_as_ul=tree_as_ul)
        if value:
            output += u"""\
            <script>
                select_node('%(value)s');
            </script>
            """ % dict(value=value)
        return mark_safe(output)


class ChainedSelectWidget(Select):
    
    def render_option(self, selected_choices, option_value, option_label):
        option_value = force_unicode(option_value)
        selected_html = (option_value in selected_choices) and u' selected="selected"' or ''
        return u'<option value="%s"%s chain_attr="%s">%s</option>' % (
            escape(option_value), selected_html,
            getattr(option_label, self.chain_attr, ''),
            conditional_escape(force_unicode(option_label)))
    
    def render(self, name, value, attrs=None, choices=()):
        if value is None: value = ''
        final_attrs = self.build_attrs(attrs, name=name)
        
        # First select - the filter
        output = [u'<select name="%s_filter"><option>--- Escolha o %s ---</option>' % (name, self.chain_attr_label)]
        for v in self.chain_attr_values:
            output.append(u'<option>%s</option>' % v)
        output.append(u'</select>')
        
        # Second select - the value
        output += [u'<select%s>' % flatatt(final_attrs)]
        options = self.render_options(choices, [value])
        if options:
            output.append(options)
        output.append(u'</select>')
        
        output.append("""<script type="text/javascript">
        (function($){
            $.fn.extend({detachOptions: function(o) {
                var s = this;
                return s.each(function(){
                    var d = s.data('selectOptions') || [];
                    s.find(o).each(function() {
                        d.push($(this).detach());
                    });
                    s.data('selectOptions', d);
                });
            }, attachOptions: function(o) {
                var s = this;
                return s.each(function(){
                    var d = s.data('selectOptions') || [];
                    for (var i in d) {
                        if (d[i].is(o)) {
                            s.append(d[i]);
                        }
                    }
                });
            }});
        })(jQuery);
        
        jQuery("select[name=%(name)s]").detachOptions("option");
        jQuery("select[name=%(name)s]").attachOptions("option[value='']");
        
        jQuery("select[name=%(name)s_filter]").change(function(){
            jQuery("select[name=%(name)s]").detachOptions("option[chain_attr!='"+jQuery(this).val()+"']");
            jQuery("select[name=%(name)s]").attachOptions("option[chain_attr='"+jQuery(this).val()+"']");
        });
        
        </script>
        """ % dict(name=name))
        
        return mark_safe(u'\n'.join(output))

class CheckboxSelectMultiplePlus(SelectMultiple):
    class Media:
        extend = False
        js = ("/static/djtools/widgets/js/marcar_todos_checkbox.js",)
    def render(self, name, value, attrs=None, choices=()):
        mark_all=''
        if value is None: 
            value = []
            mark_all = "markall"
        has_id = attrs and 'id' in attrs
        final_attrs = self.build_attrs(attrs, name=name)
        output = ['<ul class="checkboxes">']
        # Normalize to strings
        str_values = set([force_text(v) for v in value])
        for i, (option_value, option_label) in enumerate(itertools.chain(self.choices, choices)):
            # If an ID attribute was given, add a numeric index as a suffix,
            # so that the checkboxes don't all have the same ID attribute.
            if has_id:
                final_attrs = dict(final_attrs, id='%s_%s' % (attrs['id'], i))
                label_for = format_html(' for="{0}"', final_attrs['id'])
            else:
                label_for = ''

            cb = CheckboxInput(final_attrs, check_test=lambda value: value in str_values)
            option_value = (option_value)
            rendered_cb = cb.render(name, option_value)
            option_label = force_text(option_label)
            output.append(format_html('<li><label{0}>{1} {2}</label></li>',
                                      label_for, rendered_cb, option_label))
        output.append('</ul>')
        output.append(format_html('<a href="#" data-elemento="{0}" class="checkbutton btn {1}">Desmarcar Todos </a>', name, mark_all))
        return mark_safe('\n'.join(output))

    def id_for_label(self, id_):
        # See the comment for RadioSelect.id_for_label()
        if id_:
            id_ += '_0'
        return id_
