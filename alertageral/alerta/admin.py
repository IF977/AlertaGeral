from alerta.models import *
from alerta.forms import *
from django.contrib import admin

admin.site.register(TipoUnidade)
# admin.site.register(TipoPeriodicidade)

class InstituicaoAdmin(admin.ModelAdmin):

    search_fields = ('nome', 'responsavel', 'e_mail', 'telefone')
    list_display = ('nome', 'responsavel', 'e_mail', 'telefone')

admin.site.register(Instituicao, InstituicaoAdmin)

class UnidadeAdmin(admin.ModelAdmin):

    search_fields = ('nome', 'responsavel', 'e_mail', 'telefone')
    list_display = ('nome', 'responsavel', 'e_mail', 'telefone')

admin.site.register(Unidade, UnidadeAdmin)

class UsuarioAdmin(admin.ModelAdmin):

    search_fields = ('cpf', 'moderador')
    list_display = ('cpf', 'moderador')

admin.site.register(Usuario, UsuarioAdmin)
class AlertaAdmin(admin.ModelAdmin):
    search_fields = ('usuario', 'data_criacao', 'assunto', 'texto')
    list_display = ('usuario', 'data_criacao', 'assunto', 'texto')    
admin.site.register(Alerta, AlertaAdmin)
admin.site.register(Assunto)
admin.site.register(Departamento)
admin.site.register(Comentario)
admin.site.register(Resposta)