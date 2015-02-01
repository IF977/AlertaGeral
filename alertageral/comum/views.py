# -*- coding: utf-8 -*-
import django.shortcuts
from django.contrib.auth.decorators import permission_required, login_required
from django.core.mail import EmailMultiAlternatives
from django.core.mail import EmailMessage

@login_required()
def admin(request):
    return django.shortcuts.render(request, 'admin.html',locals())
    
def monta_html(conteudo, tipo):
    if str(tipo) == 'senha':
        html_alerta = 'O seu usuario AlertaGeral eh: %s e a senha eh: %s' %(conteudo[0], conteudo[1])
    elif str(tipo) == 'cadastro':
        html_alerta = 'Cadastro realizado com sucesso, seu usuario AlertaGeral eh: %s e a senha eh: %s' %(conteudo[0], conteudo[1])
    else:
        html_alerta = '<html>Teste criação de alerta: <br> Alerta %s criado </html>' %(conteudo)
    return html_alerta

def enviar_email(subject, from_email, to_email, alerta=None, tipo=None):
    subject = subject
    from_email = from_email
    message_html = monta_html(alerta, tipo)
    email = EmailMessage(subject, message_html, 'alerta.geralmail@gmail.com', to=[to_email])
    email.send(fail_silently=False)