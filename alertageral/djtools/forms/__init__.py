# -*- coding: utf-8 -*-
from django.forms import *
from djtools.formfields import *

from django.contrib.auth.models import Group, Permission

class AtribuirPermissaoForm(forms.Form):
    usuarios = forms.CharField(label=u'Usuários', required=True, widget=forms.Textarea(), help_text=u'Lista de username separada por ; ou , ou quebra de linha')
    grupos = forms.ModelMultipleChoiceField(Group.objects.all(), widget=AjaxMultiSelect(), required=False)
    permissoes = forms.ModelMultipleChoiceField(Permission.objects.all(), widget=AjaxMultiSelect(), label=u'Permissões', required=False)

class NotificacaoGrupoForm(forms.Form):
    titulo = forms.CharField(label="Título", required=True, initial='Notificação (SUAP)')
    remetente = forms.CharField(label="E-mail", required=True, help_text='E-mail do remetente')
    texto = forms.CharField(widget=forms.Textarea({'rows': 10, 'cols': 80}), required=True, label='Notificação', help_text='Texto da notificação. Pode conter quebras de linha, porém não deve conter tags HTML.')