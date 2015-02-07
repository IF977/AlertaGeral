# -*- coding: utf-8 -*-

from djtools import forms
from djtools.formwidgets import AutocompleteWidget, AjaxMultiSelect, BrDataWidget, BRCpfWidget, BRCpfCnpjWidget
from alerta.models import *

# class AlunoForm(forms.ModelForm):
    # class Meta:
        # model = Aluno
    # cpf = forms.CharField(label=u'CPF', widget=BRCpfWidget, help_text=u'XXX.XXX.XXX-XX', required=True)
    # nome = forms.CharField(label=u'Nome',
                                       # required=True,
                                       # help_text=u'Nome completo',
                                       # widget=forms.TextInput(attrs={'size':'42'}),
                                       # max_length=45)
    # matricula = forms.CharField(label=u'Matricula',
                                       # required=True,
                                       # widget=forms.TextInput(attrs={'size':'11'}),
                                       # max_length=12)
    # conta_corrente = forms.CharField(label=u'Conta Corrente',
                                       # required=False,
                                       # widget=forms.TextInput(attrs={'size':'11'}),
                                       # max_length=11)

    # def clean_cpf(self):
        # cpf = self.cleaned_data['cpf']
        # if len(cpf) < 14:
            # raise forms.ValidationError(u'CPF inválido formato deve ser XXX.XXX.XXX-XX')
        # cpf_array = []
        # cont = 10
        # d1 = d2 = 0
        # for i in range(0,14):
            # if cpf[i].isdigit():
                # cpf_array.append(int(cpf[i]))
        # for i in range(0,9):
            # d1 = cont*cpf_array[i] + d1
            # cont = cont - 1
        # cpf_array.append(11-d1%11)
        # cont = 11
        # for i in range(0,10):
            # d2 = cont*cpf_array[i] + d2
            # cont = cont - 1
        # d1 = d1%11
        # d2 = d2%11
        # if d1 < 2:
            # d1 = 0
        # else:
            # d1 = 11-d1
        # if d2 < 2:
            # d2 = 0
        # else:
            # d2 = 11-d2
        # if (cpf_array[9] != d1) | (cpf_array[10] != d2):
            # raise forms.ValidationError(u'CPF inválido - Digito verificador inválido')
        # return self.cleaned_data['cpf']

# class ConsultaForm(forms.Form):
    # cpf = forms.CharField(label=u'CPF', widget=BRCpfWidget, help_text=u'Utilize formato xxx.xxx.xxx-xx', required=True)

    # def clean_cpf(self):
        # cpf = self.cleaned_data['cpf']
        # if len(cpf) < 14:
            # raise forms.ValidationError(u'CPF inválido formato deve ser XXX.XXX.XXX-XX')
        # cpf_array = []
        # cont = 10
        # d1 = d2 = 0
        # for i in range(0,14):
            # if cpf[i].isdigit():
                # cpf_array.append(int(cpf[i]))
        # for i in range(0,9):
            # d1 = cont*cpf_array[i] + d1
            # cont = cont - 1
        # cpf_array.append(11-d1%11)
        # cont = 11
        # for i in range(0,10):
            # d2 = cont*cpf_array[i] + d2
            # cont = cont - 1
        # d1 = d1%11
        # d2 = d2%11
        # if d1 < 2:
            # d1 = 0
        # else:
            # d1 = 11-d1
        # if d2 < 2:
            # d2 = 0
        # else:
            # d2 = 11-d2
        # if (cpf_array[9] != d1) | (cpf_array[10] != d2):
            # raise forms.ValidationError(u'CPF inválido - Digito verificador inválido')
        # return self.cleaned_data['cpf']

# class PagamentoForm(forms.Form):

    # programa = forms.ModelChoiceField(
        # queryset = Programa.objects.all(),
        # required = False
    # )

# class PeriodoForm(forms.Form):

    # Ano = forms.ModelChoiceField(
        # queryset = Ano.objects.all().order_by('ano'),
        # initial = Ano.objects.all().order_by('ano')[0],
        # required = True
    # )