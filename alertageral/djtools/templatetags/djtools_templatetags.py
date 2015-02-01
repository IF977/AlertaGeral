# -*- coding: utf-8 -*-

from django import forms
from django.conf import settings
from django.contrib.admin.templatetags.admin_list import pagination, DOT
from django.contrib.admin.views.main import SEARCH_VAR, PAGE_VAR
from django.template import Library, Node, Template, Context
from django.template.base import TemplateSyntaxError
from django.template.context import RequestContext
from django.template.loader import add_to_builtins, render_to_string
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django_tables2.templatetags.django_tables2 import RenderTableNode
from djtools import formutils
from djtools.utils import get_djtools_delete_object_url, has_delete_permission, \
    get_admin_object_url, has_change_permission, has_view_permission
from xml.dom.minidom import parseString, Element
from xml.parsers.expat import ExpatError
import django
import re


register = Library()
add_to_builtins('djtools.templatetags.djtools_templatetags')
add_to_builtins('djtools.templatetags.djtools_templatefilters')


def view_object_icon(obj):
    """
    Aponta para ``obj.get_absolute_url()``
    Permissão necessária: ``change_{{ obj.__class__ }}``
    """
    if not hasattr(obj, 'get_absolute_url') or \
       (hasattr(obj, 'get_absolute_url') and not obj.get_absolute_url()) or \
       not has_view_permission(model=obj.__class__):
        return u''
    return u'<a class="icon-search" href="%(href)s" title="%(title)s">Visualizar</a>' % \
        dict(href  = obj.get_absolute_url(),
             title = (u'Ver %s' % unicode(obj))) 
register.simple_tag(view_object_icon)

def edit_object_icon(obj):
    """
    Templatetag para incluir ícone de remoção do obj, já testando se o usuário 
    autenticado tem permissões para isso.
    """
    if not has_change_permission(obj=obj):
        return u''
    return u'<a class="icon-edit" href="%(href)s" title="%(title)s">Editar</a>' % \
        dict(href  = get_admin_object_url(obj),
             title = (u'Editar %s' % unicode(obj))) 
register.simple_tag(edit_object_icon)

def delete_object_icon(obj):
    """
    Templatetag para incluir ícone de remoção do obj, já testando se o usuário 
    autenticado tem permissões para isso.
    """
    if not has_delete_permission(obj=obj):
        return u''
    return u'<a class="icon-trash confirm" href="%(href)s" title="%(title)s"></a>' % \
        dict(href  = get_djtools_delete_object_url(obj),
             title = (u'Remover %s' % unicode(obj))) 
register.simple_tag(delete_object_icon)

def dt_search_form(cl):
    return {
        'cl': cl,
        'show_result_count': cl.result_count != cl.full_result_count,
        'search_var': SEARCH_VAR,
    }
dt_search_form = register.inclusion_tag('djtools/templates/adminutils/search_form.html')(dt_search_form)

def dt_pagination(cl):
    return pagination(cl)
dt_pagination = register.inclusion_tag('djtools/templates/adminutils/pagination.html')(dt_pagination)

def dt_paginator_number(cl,i):
    if i == DOT:
        return u'<li><a href="#">...</a></li> '
    elif i == cl.page_num:
        return mark_safe(u'<li class="active"><a href="#">%d</a></li> ' % (i+1))
    else:
        return mark_safe(u'<li><a href="%s"%s>%d</a></li> ' \
            % (escape(cl.get_query_string({PAGE_VAR: i})), 
               (i == cl.paginator.num_pages-1 and ' class="end"' or ''), 
               i+1))
dt_paginator_number = register.simple_tag(dt_paginator_number)

################################################################################
# {% render_form %}

class RenderFormNode(Node):
    def __init__(self, form_name, render_full=True):
        self.form_name = form_name
        self.render_full = render_full
    
    def render(self, context):
        form = context[self.form_name]
        if not hasattr(form, 'SUBMIT_LABEL'):
            if isinstance(form, forms.ModelForm):
                form.SUBMIT_LABEL = u'Salvar'
            else:
                form.SUBMIT_LABEL = u''
        form.rendered = formutils.render_form(form)
        form.ID = form.__class__.__name__.lower().replace('form', '_form')
        return render_to_string(
            template_name    = 'djtools/templates/form.html', 
            dictionary       = dict(form=form, render_full=self.render_full),
            context_instance = RequestContext(context['request']))

@register.tag
def render_form(parser, token):
    """
    Renderiza o form considerando seu atributo fieldsets
    
    {% render_form form render_full=True %}
    
    O ``render_full`` por padrão é True e define que o formulário será renderizado
    totalmente, com mensagens de validação e a própria tag form. Caso seja False,
    será renderizado apenas o form, como o form.as_table.
    """
    contents_splited = token.split_contents()
    if len(contents_splited) == 2:
        tag_name, form_name = contents_splited
        render_full = True
    elif len(contents_splited) == 3:
        tag_name, form_name, render_full = contents_splited
        render_full = not render_full in ('0', 'False')
    return RenderFormNode(form_name, render_full)

################################################################################
# {% box %}

class RenderBox(Node):
    
    def __init__(self, nodelist, title, classnames):
        self.nodelist = nodelist
        # retirando as aspas de `title` e `classnames`
        self.title = (title or u'')[1:-1] 
        self.classnames = (classnames or u'')[1:-1]
    
    def render(self, context):
        title = Template(self.title).render(Context(context))
        content = re.sub(r'[\t\n\r]', '', self.nodelist.render(context))
        
        # indica se haverá margin entre a caixa de conteúdo interno e a borda da box
        marginless = False
        
        try:
            """ verifica se existe um nó principal, ou seja, 
            se existe apenas uma tag (div, table, p, etc), englogando todo o conteúdo """
            root_node = parseString(content.encode('utf-8')).documentElement 
            if root_node.nodeName == 'table' and root_node.getAttribute('class') != 'info':
                marginless = True
                
        except ExpatError:
            """se chegou aqui é porque existem vários nós (tags html) no mesmo nível"""
            pass
        
        finally:
            content = self.nodelist.render(context)
            return render_to_string('djtools/templates/box.html', 
                                    dict(title      = title, 
                                         classnames = self.classnames, 
                                         content    = content, 
                                         marginless = marginless)) 

@register.tag(name="box")
def do_box(parser, token):
    nodelist = parser.parse(('endbox',))
    contents_splited = token.split_contents()
    if len(contents_splited) == 2:
        tag_name, title = contents_splited
        classnames = None
    elif len(contents_splited) == 3:
        tag_name, title, classnames = contents_splited
    else:
        raise Exception(u'A templatetag box deve conter apenas o título.')
    parser.delete_first_token()
    return RenderBox(nodelist, title, classnames)


@register.simple_tag
def media_filter_box():
    return u'<link type="text/css" rel="stylesheet" href="/static/djtools/filter_box/css/filter_box.css" /><script type="text/javascript" src="/static/djtools/filter_box/js/filter_box.js"></script>'


@register.tag(name="filter_box")
def do_filter_box(parser, token):
    nodelist = parser.parse(('endfilter_box',))
    contents_splited = token.split_contents()
    if len(contents_splited) == 1:
        expansible = False
        expanded = True
    elif len(contents_splited) == 2:
        tag_name, expanded = contents_splited
        expansible = True
        expanded = expanded not in ('0', 'False')
    parser.delete_first_token()
    return RenderFilterBox(nodelist, expansible, expanded)


class RenderFilterBox(Node):
    def __init__(self, nodelist, expansible=False, expanded=True):
        self.nodelist = nodelist
        self.expansible = expansible
        self.expanded = expanded

    def render(self, context):
        content = re.sub(r'[\t\n\r]', '', self.nodelist.render(context))
        data = []
        pairs = 0

        try:
            root_node = parseString(content.encode('utf-8')).documentElement
            if root_node.nodeName == 'table':
                for row_tag in root_node.childNodes:
                    if row_tag.nodeType == Element.ELEMENT_NODE and row_tag.nodeName == 'tr':
                        row = []
                        
                        item_tags = []
                        for child in row_tag.childNodes:
                            if child.nodeType == Element.ELEMENT_NODE and child.nodeName == 'td':
                                item_tags.append(child)
                        
                        n_elem = len(item_tags)
                        for i in range(0, n_elem, 2):
                            # é preciso testar para evitar extrair conteúdo de tags <td> sem conteúdo
                            if item_tags[i].firstChild:
                                if item_tags[i].firstChild.nodeType == Element.TEXT_NODE:
                                    key = item_tags[i].firstChild.toxml() + ':'
                                else:
                                    key = item_tags[i].firstChild.toxml()
                            else:
                                # é repassado string vazia quando a tag <td> não possui conteúdo
                                key = ''
    
                            # verifica se existe algum par chave/valor em que foi repassado apenas a chave e neste case
                            # repassa a string '!@#' que é tratada pelo template para que não seja apresentado nenhum default
                            if (n_elem%2) !=0 and i == n_elem-1:
                                value = '!@#'
                            elif item_tags[i+1].firstChild:
                                value = item_tags[i+1].firstChild.toxml()
                            else:
                                value = ''

                            # o None é substituído por que em alguns casos o termo é enviado pelo template que chamou o templatetag
                            row.append([key.replace('None',''), value.replace('None','')])

                        data.append(row)

                for row in data:
                    if len(row) > pairs:
                        pairs = len(row)
                
                return render_to_string('djtools/templates/render_filter_box.html', 
                                        dict(data=data, expansible=self.expansible, expanded=self.expanded, max_pairs=pairs))
            
        except:
            raise

@register.simple_tag
def debug_info():
    bd = settings.DATABASES['default']
    return u'Django <strong>%s</strong> | Project path: <strong>%s</strong> | Database: <strong>%s %s@%s:%s</strong>' \
        % (django.get_version(), settings.PROJECT_PATH, bd['NAME'], bd['USER'], 
           bd['HOST'], bd['PORT'])

@register.simple_tag
def google_analytics():
    """Insere o código js necessário para o tracking no google analytics.
    Para isso deve-se definir a variável settings.DJTOOLS_GOOGLE_ANALYTICS_ID"""
    if not getattr(settings, 'DJTOOLS_GOOGLE_ANALYTICS_ID', None):
        return u''
    return u'''<script type="text/javascript">
var _gaq = _gaq || [];
_gaq.push(['_setAccount', '%s']);
_gaq.push(['_trackPageview']);

(function() {
    var ga = document.createElement('script'); ga.type = 'text/javascript'; ga.async = true;
    ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';
    var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(ga, s);
})();
</script>''' % settings.DJTOOLS_GOOGLE_ANALYTICS_ID


@register.tag(name="getattr_plus")
def getattr_plus(obj, args):
    """ Try to get an attribute from an object.
    Example: {% if block|getattr_plus:"editable,True" %}
    Beware that the default is always a string, if you want this
    to return False, pass an empty second argument:
    {% if block|getattr_plus:"editable," %}
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


@register.tag(name="render_table")
def render_table(parser, token):
    bits = token.split_contents()
    try:
        tag, table = bits.pop(0), parser.compile_filter(bits.pop(0))
    except ValueError:
        raise TemplateSyntaxError("'%s' must be given a table or queryset."
                                  % bits[0])
    
    template = parser.compile_filter(bits.pop(0)) if bits else parser.compile_filter(u'"table_plus.html"')
    return RenderTableNode(table, template)

