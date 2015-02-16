# -*- coding: utf-8 -*-

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
import random, datetime
from alerta.forms import *
from django.contrib.auth.models import User

@login_required
def cadastrar_alerta(request):
    if request.method == "POST":
        form = AlertaForm(request.POST)
        if form.is_valid():
           # try except disponibilizado para permitir que alertas sem imagens e marcacao
		   # funcione
           try:
               img = request.FILES['imagem']
           except:
               img = 'imagens/padrao.jpg'
           try:
               anonimo = request.POST['anonimo']
               anonimo = True
           except:
		       anonimo = False
           ass = Assunto.objects.get(id=int(request.POST['assunto']))
           comentario = request.POST['comentario']
           usuario = request.user
           alerta = Alerta.objects.create(usuario=usuario, data_criacao=datetime.date.today(),\
           assunto=ass, imagem=img, texto=comentario, anonimo=anonimo)
           tipo = 'alerta'
           inf = [comentario]
           e_mail1 = usuario.email
           e_mail2 = ass.departamento.e_mail
           enviar_email('Novo Alerta Cadastrado', 'alertageral@gmail.com', e_mail2, inf, tipo)
           enviar_email('Novo Alerta Cadastrado', 'alertageral@gmail.com', e_mail1, inf, tipo)
        return django.shortcuts.render(request, 'confirmaenviaalerta.html',locals())
        
    else:
        form = AlertaForm()
        # Se for super usuário todos os alertas são carregados
    if request.user.is_superuser:
        assuntos = Assunto.objects.all()
        alertas = Alerta.objects.filter(ativo=True).order_by('-id')
    else:
        usuario = Usuario.objects.get(username=request.user.username)
        unidade = usuario.unidade
        assuntos = Assunto.objects.filter(departamento__unidade=unidade)
        alertas = Alerta.objects.filter(usuario=usuario,ativo=True).order_by('-id')
    return django.shortcuts.render(request, 'cadastroalerta.html',locals())

@login_required
def comentarios(request, alerta_id):
    if request.method == "POST":
       alerta = Alerta.objects.get(id=int(alerta_id))
       coment = request.POST['comentario']
       comentario = Comentario.objects.create(usuario=request.user, alerta=alerta, data_criacao=datetime.date.today(),\
       texto=coment)
       alerta = Alerta.objects.get(id=alerta_id)
       comentarios = Comentario.objects.filter(alerta=alerta).order_by('-id')
       respostas = Resposta.objects.filter(alerta=alerta).order_by('-id')
       return django.shortcuts.render(request, 'comentarios.html',locals())
    else:
        alerta = Alerta.objects.get(id=alerta_id)
        comentarios = Comentario.objects.filter(alerta=alerta).order_by('-id')
        respostas = Resposta.objects.filter(alerta=alerta).order_by('-id')
    return django.shortcuts.render(request, 'comentarios.html',locals())

@login_required
def validar_responder_alerta(request, alerta_id):
    if request.method == "POST":
       alerta = Alerta.objects.get(id=alerta_id)
       try:
	       chave = request.POST['chave']
       except:
           return django.shortcuts.render(request, 'loginchave.html',locals())
       chave_departamento = alerta.assunto.departamento.chave
       if chave == chave_departamento:
           # a seguranca de poder responder deve ser melhorada
           # nao houve tempo habil para desenvolver esta funcao
		   # o controle de permissoes de usuario deve ser mais seguro
		   # mas o requisito inicial preve essa chave de permissao
           pode_responder = '8i234sdcskckishbHBVTVy@734794hb@jhbi#$bibyibiuyB@iybUI#ibiyby6382'
           return django.shortcuts.render(request, 'respostas.html',locals())
       else:
           pode_responder = '8i234sdcskckishbHBVTVy@734794hb@jhdi#$bibyibiuyB@iybUI#ibiyby6382'
           erro = 'Chave incorreta'
           return django.shortcuts.render(request, 'loginchave.html',locals())
    return django.shortcuts.render(request, 'comentarios.html',locals())

@login_required
def responder_alerta(request, alerta_id):
    if request.method == "POST":
       if request.POST['texto'] == '8i234sdcskckishbHBVTVy@734794hb@jhbi#$bibyibiuyB@iybUI#ibiyby6382':
           alerta = Alerta.objects.get(id=int(alerta_id))
           resposta = request.POST['resposta']
           res = Resposta.objects.create(usuario=request.user,alerta=alerta,data_criacao=datetime.date.today(),texto=resposta)
           respostas = Resposta.objects.filter(alerta=alerta).order_by('-id')
           mensagem = 'Resposta cadastrada com sucesso'
           return django.shortcuts.render(request, 'respostas.html',locals())
       else:
           pass
    return django.shortcuts.render(request, 'comentarios.html',locals())

def todosalertas(request):
    alertas = Alerta.objects.filter(ativo=True).order_by('-id')

    return django.shortcuts.render(request, 'todosalertas.html',locals())
    
def recentes_alertas(request):
    alertas = Alerta.objects.filter(ativo=True).order_by('-id')[:12]
    
    return django.shortcuts.render(request, 'recentesalertas.html',locals())

def cadastro(request):
    if request.method == "POST":
        un = Unidade.objects.get(id=int(request.POST['unidade']))
        nome = str(request.POST['nome'])
        apelido = str(request.POST['apelido'])
        cpf = str(request.POST['cpf'])
        mail = str(request.POST['mail'])
        telefone = str(request.POST['telefone'])
        senha = str(request.POST['senha'])
        us = Usuario.objects.create(cpf=cpf,apelido=apelido,telefone=telefone,\
        password=senha,username=cpf, first_name=nome,email=mail, unidade=un)
        us.set_password(us.password)
        u = Usuario.objects.filter(id=us.pk).update(password=us.password)
        inf = [us.username,senha]
        tipo = 'cadastro'
        try:
            enviar_email('Cadastro Alerta Geral', 'alertageral@gmail.com', us.email, inf, tipo)
        except:
            mensagem = 'O cadastro foi realizado mas houve falha no envio do e-mail, tente acessar o sistema'
            return django.shortcuts.render(request, 'confirmacadastro.html',locals())
        return django.shortcuts.render(request, 'confirmacadastro.html',locals())
    else:
        unidades = Unidade.objects.all()
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
            mensagem = 'Nao foi possivel enviar o e-mail contate o administrador do sistema exemplo@exemplo.com'
            return django.shortcuts.render(request, 'recuperasenha.html',locals())
    else:
        return django.shortcuts.render(request, 'recuperasenha.html',locals())
