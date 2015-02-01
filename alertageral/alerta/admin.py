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
    pass
admin.site.register(Alerta, AlertaAdmin)
admin.site.register(Assunto)
admin.site.register(Departamento)


# class AlunoAdmin(admin.ModelAdmin):
    
    # form = AlunoForm
    # filter_horizontal = ('programa',)
    # search_fields = ('cpf', 'nome', 'matricula')
    # list_display = ('nome', 'cpf', 'matricula', 'vinculado', 'banco', 'agencia', 'conta_corrente', 'renda_percapta', 'interno', 'e_mail')
        
# admin.site.register(Aluno, AlunoAdmin)

# # admin.site.register(TipoPrograma)

# class ProgramaAdmin(admin.ModelAdmin):

    # search_fields = ('descricao', 'ano')
    # list_display = ('descricao', 'ano', 'valor_previsto')

# admin.site.register(Programa, ProgramaAdmin)
# admin.site.register(Imagem)
# admin.site.register(OrigemRecurso)
# admin.site.register(Ano)

# class PagamentoAdmin(admin.ModelAdmin):
    # # form = PagamentoForm
    # search_fields = ('data', 'valor', 'programa', 'ob', 'aluno', 'status')
    # list_display = ('programa', 'data', 'aluno', 'valor', 'status')
# admin.site.register(Pagamento, PagamentoAdmin)

# admin.site.register(Noticia)