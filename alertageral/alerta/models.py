from django.db import models
from django.contrib.auth.models import User
from comum.views import enviar_email
from django.core.exceptions import ValidationError

class Instituicao(models.Model):
    nome = models.CharField(max_length=50)
    responsavel = models.CharField(max_length=50)
    e_mail = models.EmailField(max_length=50, verbose_name='E-mail')
    telefone = models.CharField(max_length=13, help_text='Ex. (xx)xxxx-xxxx')

    class Meta:
        verbose_name_plural = 'Instituicoes'

    def __unicode__(self):
        return self.nome

    def save(self, *args, **kwargs):
        if (Instituicao.objects.count() > 0 and self.id != Instituicao.objects.get().id):
            raise ValidationError("Limitado a 1 instancia")
        super(Instituicao, self).save(*args, **kwargs)

        
class TipoUnidade(models.Model):
    descricao = models.CharField(max_length=50)

    class Meta:
        verbose_name_plural = 'Tipos Unidades'
        
    def __unicode__(self):
        return self.descricao

class Unidade(models.Model):
    nome = models.CharField(max_length=50)
    responsavel = models.CharField(max_length=50)
    e_mail = models.EmailField(max_length=50, verbose_name='E-mail')
    telefone = models.CharField(max_length=13, help_text='ex. (xx)xxxx-xxxx')
    instituicao = models.ForeignKey(Instituicao)
    tipo = models.ForeignKey(TipoUnidade)

    def __unicode__(self):
        return self.nome

class Departamento(models.Model):
    nome = models.CharField(max_length=50)
    responsavel = models.CharField(max_length=50)
    e_mail = models.EmailField(max_length=50, verbose_name='E-mail')
    telefone = models.CharField(max_length=13, help_text='ex. (xx)xxxx-xxxx')
    telefone = models.CharField(max_length=13, help_text='ex. (xx)xxxx-xxxx')
    unidade = models.ForeignKey(Unidade)
    chave = models.CharField(max_length=20, help_text='Chave de acesso para responder alerta max 20 caracteres')

    def __unicode__(self):
        return self.nome

class Assunto(models.Model):
    nome = models.CharField(max_length=50)
    departamento = models.ForeignKey(Departamento)

    def __unicode__(self):
        return self.nome

class Usuario(User):
    unidade = models.ForeignKey(Unidade)
    cpf = models.CharField(max_length=14, unique=True)
    apelido = models.CharField(max_length=20)
    moderador = models.BooleanField(default=False)
    telefone = models.CharField(max_length=13, help_text='ex. (xx)xxxx-xxxx', blank=True, null=True)
    
    def __init__(self, *args, **kwargs):
        super(Usuario, self).__init__(*args, **kwargs)
        self.can_delete = False
        
    def save(self, *args, **kwargs):
        # do anything you need before saving
        super(Usuario, self).save(*args, **kwargs)
        us = Usuario.objects.get(id=self.pk)
        us.set_password(us.password)
        u = Usuario.objects.filter(id=self.pk).update(password=us.password)
    def __unicode__(self):
        return self.cpf

class Alerta(models.Model):
    usuario = models.ForeignKey(User)
    data_criacao = models.DateField()
    assunto = models.ForeignKey(Assunto)
    # unidade = models.ForeignKey(Unidade) # Relacionado com assunto
    # departamento = models.ForeignKey(Departamento) # Relacionado com assunto
    imagem = models.ImageField('Imagem', upload_to='imagens', blank=True)
    texto = models.TextField()
    anonimo = models.BooleanField(default=False)
    ativo = models.BooleanField(default=True)
    
    def save(self, *args, **kwargs):
        # do anything you need before saving
        if self.pk is None:
            tipo = 'alerta'
            try:
                enviar_email('Novo Alerta', 'alertageral@gmail.com', self.usuario.email, self.assunto, tipo)
            except:
                pass
        super(Alerta, self).save(*args, **kwargs)
        
    def __unicode__(self):
        return '%s - %s' %(self.usuario, self.assunto.nome)
        
class Comentario(models.Model):
    usuario = models.ForeignKey(User)
    alerta = models.ForeignKey(Alerta)
    data_criacao = models.DateField()
    texto = models.TextField()

    def __unicode__(self):
        return '%s - %s' %(self.usuario, self.texto)

class Resposta(models.Model):
    usuario = models.ForeignKey(User)
    alerta = models.ForeignKey(Alerta)
    data_criacao = models.DateField()
    texto = models.TextField()

    def __unicode__(self):
        return '%s - %s' %(self.usuario, self.texto)