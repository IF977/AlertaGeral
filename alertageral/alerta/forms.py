# -*- coding: utf-8 -*-

from djtools import forms
from djtools.formwidgets import *
from alerta.models import *

class AlertaForm(forms.ModelForm):
    class Meta:
        model = Alerta
        fields = ['imagem']
        
        imagem = forms.ImageField(required=True)

    # def clean_cpf(self):
        # cpf = self.cleaned_data['cpf']
        # if len(cpf) < 14:
            # raise forms.ValidationError(u'CPF inválido formato deve ser XXX.XXX.XXX-XX')
            # d2 = 11-d2
        # if (cpf_array[9] != d1) | (cpf_array[10] != d2):
            # raise forms.ValidationError(u'CPF inválido - Digito verificador inválido')
        # return self.cleaned_data['cpf']