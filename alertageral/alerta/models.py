from django.db import models
from django.contrib.auth.models import User
from comum.views import enviar_email

class Instituicao(models.Model):
    nome = models.CharField(max_length=50)
    responsavel = models.CharField(max_length=50)
    e_mail = models.EmailField(max_length=50, verbose_name='E-mail')
    telefone = models.CharField(max_length=13, help_text='Ex. (xx)xxxx-xxxx')

    class Meta:
        verbose_name_plural = 'Instituicoes'

    def __unicode__(self):
        return self.nome

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
    unidade = models.ForeignKey(Unidade)

    def __unicode__(self):
        return self.nome

class Assunto(models.Model):
    nome = models.CharField(max_length=50)
    departamento = models.ForeignKey(Departamento)

    def __unicode__(self):
        return self.nome

class Usuario(User):
    cpf = models.CharField(max_length=14)
    apelido = models.CharField(max_length=20)
    moderador = models.BooleanField(default=False)
    telefone = models.CharField(max_length=13, help_text='ex. (xx)xxxx-xxxx')
    
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
    usuario = models.ForeignKey(Usuario)
    data_criacao = models.DateField()
    assunto = models.ForeignKey(Assunto)
    unidade = models.ForeignKey(Unidade) # Eh necessario ja temos departamento que tem unidade?
    departamento = models.ForeignKey(Departamento)
    imagem = models.ImageField('Imagem', upload_to='imagens', blank=True)
    #video seria interessante upload de arquivos em geral e tratarmos as extensoes possiveis
    # quando o usuario quizer ver ele baixa
    texto = models.TextField()
    
    def save(self, *args, **kwargs):
        # do anything you need before saving
        if self.pk is None:
            tipo = 'alerta'
            enviar_email('Novo Alerta', 'alertageral@gmail.com', self.usuario.email, self.assunto, tipo)
        super(Alerta, self).save(*args, **kwargs)
        
    def __unicode__(self):
        return '%s - %s' %(self.usuario, self.assunto.nome)
        
class Comentario(models.Model):
    usuario = models.ForeignKey(Usuario)
    alerta = models.ForeignKey(Alerta)
    data_criacao = models.DateField()
    texto = models.TextField()

    def __unicode__(self):
        return '%s - %s' %(self.usuario, self.assunto.nome)

class Resposta(models.Model):
    usuario = models.ForeignKey(Usuario)
    alerta = models.ForeignKey(Alerta)
    data_criacao = models.DateField()
    texto = models.TextField()

    def __unicode__(self):
        return '%s - %s' %(self.usuario, self.assunto.nome)