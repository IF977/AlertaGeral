# -*- coding: utf-8 -*-

from django.contrib import messages
from django.contrib.auth.decorators import permission_required, login_required
from django.contrib.auth.models import Group, Permission, User
from django.db.models import get_model
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.datastructures import SortedDict
from djtools.forms import AtribuirPermissaoForm, NotificacaoGrupoForm
from djtools.management.permission import GroupPermission
from djtools.models import GroupManagement
from djtools.utils import httprr, rtr, has_delete_permission


def delete_object(request, app, model, pk):
    """
    View genérica para remover um objeto de modelo.
    -----
    Parâmetro opcional no GET: ``redirect_url``.
    """
    
    # Pegando a classe de modelo e o objeto
    model_class = get_model(app, model)
    obj = get_object_or_404(model_class, pk=pk)
    
    if not has_delete_permission(obj=obj, user=request.user):
        return HttpResponseForbidden()
    
    # Removendo o objeto
    obj.delete()
    
    # redirect_url
    if 'redirect_url' in request.GET:
        redirect_url = request.GET['redirect_url']
    else:
        redirect_url = request.META.get('HTTP_REFERER', '/')
    
    # msg
    msg_args = dict(name=model_class._meta.verbose_name.title(), obj=unicode(obj))
    msg = u'%(name)s "%(obj)s" foi removido com sucesso.' % msg_args
    
    return httprr(redirect_url, msg)


@rtr()
@login_required()
@permission_required('auth.can_change_user')
def give_permission(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden()
    elif request.method=='POST' and 'confirmacao' not in request.POST:
        form = AtribuirPermissaoForm(data=request.POST)
        if form.is_valid():
            usuarios = form.cleaned_data['usuarios']
            usuarios = usuarios.replace(',', ';').replace('\r\n', ';')
            grupos = form.cleaned_data['grupos']
            permissoes = form.cleaned_data['permissoes']
            lista_usuarios = []
            lista_usuarios_nao_identificados = []
            for login in usuarios.split(';'):
                if login:
                    login = login.strip()
                    usuario_qs = User.objects.filter(username=login)
                    if usuario_qs:
                        lista_usuarios.append(usuario_qs[0])
                    else:
                        lista_usuarios_nao_identificados.append(login)
            l = []
            for usuario in lista_usuarios:
                l.append(unicode(usuario.pk))
            usuarios_str = ';'.join(l)
            l = []
            for grupo in grupos:
                l.append(unicode(grupo.pk))
            grupos_str = ';'.join(l)
            l = []
            for permissao in permissoes:
                l.append(unicode(permissao.pk))
            permissoes_str = ';'.join(l)    
    elif request.method=='POST' and 'confirmacao' in request.POST:
        form = AtribuirPermissaoForm()
        usuarios_str = request.POST['usuarios']
        grupos_str =  request.POST['grupos']
        permissoes_str =  request.POST['permissoes']
        
        grupos = []
        for id in grupos_str.split(';'):
            if id:
                grupos.append(Group.objects.get(pk=id))
        permissoes = []
        for id in permissoes_str.split(';'):
            if id:
                permissoes.append(Permission.objects.get(pk=id))
        for id in usuarios_str.split(';'):
            usuario = User.objects.get(pk=id)
            for grupo in grupos:
                usuario.groups.add(grupo)
            for permissao in permissoes:
                usuario.user_permissions.add(permissao)
            usuario.save()
        httprr("/djtools/give_permission/", u'Permissões atribuídas com sucesso')
    else:
        form = AtribuirPermissaoForm()
    return locals()

def breadcrumbs_reset(request, menu_item_id, url):
    if request.META['QUERY_STRING']:
        url += '?%s' % request.META['QUERY_STRING']
    bc = SortedDict()
    bc[u'Início'] = '/'
    request.session['bc'] = bc
    request.session['menu_item_id'] = menu_item_id
    return HttpResponseRedirect('/%s'%url)

@rtr()
def notificar_grupo(request, pk_grupo):
    grupo = Group.objects.get(pk=pk_grupo)

    if not GroupManagement.user_can_manage(request.user):
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = NotificacaoGrupoForm(request.POST)
        if form.is_valid():
            titulo = form.cleaned_data['titulo']
            remetente = form.cleaned_data['remetente']
            texto = form.cleaned_data['texto']
            n = 0;
            count = 0;
            for usuario in grupo.user_set.all():
                try:       
                    n += 1
                    count += 1
                    usuario.email_user(titulo, texto, remetente)
                except:
                    n -= 1
            messages.info(request, u'Notificações (%d/%d) enviadas com sucesso' % (n, count))
            return locals()
    else:
        form = NotificacaoGrupoForm()
    return locals()

@rtr()
@login_required()
def permissions(request, app):
    if not request.user.is_superuser:
        return HttpResponseForbidden()
    title = u'Permissões por Grupo'
    groupPermission = GroupPermission(app)
    groupPermission.process('%s/permissions.xml' % app)
    groups = groupPermission.groups
    
    data = []
    for permission in Permission.objects.filter(content_type__app_label=app):
        permission.groups = []
        permission.verbose_name = permission.name.replace('Can add', 'Cadastrar').replace('Can change', 'Alterar').replace('Can delete', 'Excluir')
        for group in groups:
            has_perm = False
            for model in group.getModels():
                for p in model.getPermissions():
                    if permission.codename == p.name:
                        has_perm = True
                        break
            permission.groups.append(has_perm)
        data.append(permission)
    return locals()