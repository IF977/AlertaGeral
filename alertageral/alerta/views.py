# -*- coding: utf-8 -*-

# from django.shortcuts import render_to_response
import django.shortcuts
from django.contrib.auth.decorators import login_required, permission_required
from djtools.utils import rtr, httprr, str_to_dateBR, group_required, \
    user_has_profile, user_has_one_of_perms, get_rss_links, to_ascii
from django.template import RequestContext
from alerta.forms import *
from alerta.models import *
from django.db.models import Count, Sum
from djtools import db
from comum.views import enviar_email
import random

@login_required
def cadastrar_alerta(request):
    alertas = Alerta.objects.all()
    # imagem_lista = []
    # for i in imagens:
        # imagem_lista.append(i.imagem)
    return django.shortcuts.render(request, 'todosalertas.html',locals())

def todosalertas(request):
    alertas = Alerta.objects.all()
    # imagem_lista = []
    # for i in imagens:
        # imagem_lista.append(i.imagem)
    return django.shortcuts.render(request, 'todosalertas.html',locals())

def cadastro(request):
    if request.method == "POST":
        try:
            nome = str(request.POST['nome'])
            apelido = str(request.POST['apelido'])
            cpf = str(request.POST['cpf'])
            mail = str(request.POST['mail'])
            telefone = str(request.POST['telefone'])
            senha = str(request.POST['senha'])
            us = Usuario.objects.create(cpf=cpf,apelido=apelido,telefone=telefone,\
            password=senha,username=cpf, first_name=nome,email=mail)
            us.set_password(us.password)
            u = Usuario.objects.filter(id=us.pk).update(password=us.password)
            inf = [us.username,senha]
            tipo = 'cadastro'
            try:
                enviar_email('Cadastro Alerta Geral', 'alertageral@gmail.com', us.email, inf, tipo)
            except:
                pass
            return django.shortcuts.render(request, 'confirmacadastro.html',locals())
        except:
            return django.shortcuts.render(request, 'cadastro.html',locals())
    else:
        return django.shortcuts.render(request, 'cadastro.html',locals())

def cria_senha(tamanho):
        caracters = '0123456789abcdefghijlmnopqrstuwvxz@#&'
        senha = ''
        for char in xrange(tamanho):
                senha += random.choice(caracters)
        return  senha

def recupera_senha(request):
    if request.method == "POST":
        try:
            senha = cria_senha(6)
            us = Usuario.objects.filter(email=request.POST['mail'])
            u = us[0]
            u.set_password(senha)
            us1 = Usuario.objects.filter(id=u.pk).update(password=u.password)
            tipo = 'senha'
            inf = [u.username,senha]
            enviar_email('Recupera Senha Alerta Geral', 'alertageral@gmail.com', us[0].email, inf, tipo)
            return django.shortcuts.render(request, 'confirmarecuperasenha.html',locals())
        except:
            return django.shortcuts.render(request, 'recuperasenha.html',locals())
    else:
        return django.shortcuts.render(request, 'recuperasenha.html',locals())