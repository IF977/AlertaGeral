# -*- coding: utf-8 -*-
"""
    Biblioteca destinada a criação de gráficos nas páginas HTML.
    Utiliza a bibliotea javascript Highchart disponível em http://www.highcharts.com.
    Os gráficos gerados podem ser exportados para diversos formatos, inclusive JPG, PNG e PDF.
    Duas categorias de gráficos foram definidas:
        - Gráficos 1D: Possuem apenas uma dimensão e podem ser exibidos sob a forma de Pizza
                    ou Rosca (possuir uma cavidade sob o eixo central).
                      São adequados para exibir totalizadores. Ex: Número de servidores por UO.
        - Gráficos 2D: Possuem duas dimensões e podem ser exibidos sob a forma de Barra (colunas
                    horizontais), Coluna (colunas verticais) e Linha (linhas verticais).
                      São adequados para exibir a evolução dos dados ao longo do tempo.
                      Ex: Número de servidores por UO nos primeiro e segundo simestre de um determinado
                      ano.
    A seguir serão mostrados códigos para construção de gráficos 1D e 2D respectivamente.
    
    g1 = Pizza()
    g1.set_titulo('Gráfico de Navegadores')
    g1.set_subtitulo('Estatística Trimestral')
    g1.formatar_dica('<b>{rotulo}</b> : {valor} %')
    g1.adicionar_dado("Firefox", 30)
    g1.adicionar_dado("IE", 15)
    g1.configurar_legenda(30, 10, 'vertical')
    g1.set_tamanho(800, 400)
    
    g2 = Linha()
    g2.set_titulo('Gráfico de Navegadores')
    g2.set_subtitulo('Estatística Trimestral')
    g2.formatar_dica('<b>{rotulo}</b> : {valor} %')
    g2.configurar_categorias('Número de Usuários', ['Primeiro', 'Segundo', 'Terceiro', 'Quarto'])
    g2.adicionar_serie('Firefox', [3, 5, 7, 2])
    g2.adicionar_serie('IE', [2, 4, 9, 5])
    g2.configurar_legenda(30, 10, 'vertical')
    g2.set_tamanho(800, 400)
"""
from django.template.loader import render_to_string
from django.utils import simplejson
from django.utils.safestring import SafeUnicode

"""
    Classe abstrata para os gráficos 1D e 2D.
    Não deve ser instanciada.
    Possui métodos comuns a todos os gráficos.
"""

class Grafico:
    def set_titulo(self, titulo):
        self.titulo = titulo
    def set_subtitulo(self, subtitulo):
        self.subtitulo = subtitulo    
    def configurar_legenda(self, x, y, orientacao):
        self.legenda_x = x
        self.legenda_y = y
        self.orientacao_legenda = orientacao
    def set_tamanho(self, comprimento, altura):
        self.comprimento = comprimento
        self.altura = altura
"""
    Classe abstrata para os gráficos 1D
    Não deve ser instanciada.
    Possui métodos comuns aos gráficos do tipo Pizza e Rosca.
"""            
class Grafico1D(Grafico):
    """
        Adiciona um novo dado ao gráfico. Ou seja, supondo que se deseje exibir o número de servidores por UO,
        um dado para esse gráfico é formado pelo nome da UO e o número de servidores nela contida. Ex: (CNat, 1208)
            nome: string contendo o nome do dado
            valor: número inteiro ou decimal contendo o valor do dado.
    """
    def adicionar_dado(self, nome, valor):
        self.dados.append((nome, valor))
    
    """
        Formata a mensagem que é mostrada ao usuário ao posicionar o cursor do mouse sob o dado.
            str: string de formatação. Deve conter dois padrões de texto. O primeiro deles está associado ao rótulo, enquanto que
            o segundo a seu valor. Ex: supondo que se deseje exibir o número de servidores por UO, a string de
            formatação '{rotulo} : {valor}' será exibida ao usuário como sendo 'CNat: 1208' caso o dado em questão tenha sido
            adicionado com o rótulo 'CNat' e o valor 1208.
            Qualquer formatação HTML pode ser aplicada. Por exemplo, '<b>{rotulo}</b> : {valor}'
    """
    def formatar_dica(self, str):
        self.formatacao_tooltip = str.replace('{rotulo}', '\'+ this.point.name +\'').replace('{valor}', '\'+ this.y +\'')    
    
    """
        Renderiza o template do gráfico de acordo com os valores de seus atributos.
        Utiliza o arquivo grafico1D.html
    """
    def __unicode__(self):
        return render_to_string('graficos/grafico1D.html', {'g' : self}) 
        
"""
    Classe abstrata para os gráficos 2D.
    Não deve ser instanciada.
    Possui métodos comuns aos gráficos do tipo Coluna, Barra e Linha.
"""
class Grafico2D(Grafico):
    def __init__(self):
        self.series = []
    """
        Configura o eixo das categorias. Ou seja, supondo que se deseje exibir a evolução de um
        determinado dado ao longo do tempo, as categorias poderiam ser os meses do ano, os semestres ou
        qualquer outro intervalo.
            titulo: Uma string contendo a descrição da unidade que está sendo medida. Ex: Valor do Orçamento
            lista_categorias: Uma lista de string contendo os valores das categorias. Ex: Jan, Fev, Mar, etc
            menor_valor: Limite inferior para os valores do eixo ortogonal ao eixo das categorias. Ex: Supondo que se deseje
                exibir o orçamento de cada UO nos dois semestres do ano, caso o menor_valor seja definido
                como 500.000, apenas valores superiores a esse valor serão mostrados no gráfico. Esse parâmetro
                serve para evitar intervalo vazios quando os dados tratam de valores muito elevados.
    """
    def configurar_categorias(self, unidade_medida, lista_categorias, menor_valor = 0):
        self.categorias = simplejson.dumps(lista_categorias)
        self.titulo_eixo = unidade_medida
        self.menor_valor = menor_valor

    """
        Adiciona uma nova série ao gráfico. Ou seja, supondo que se deseje exibir o orçamento de cada UO nos
        dois semestres do ano, uma série é uma formada pela nome da UO e dos valores do orçamentos nos respectivos
        semestres. Ex: (CNat, [3000000, 2498000, 3989082]).
            nome: string contendo o nome da série.
            lista_dados: lista de dados numéricos contendo os valores da série. Deve possuir o mesmo número de elementos
                da lista de categorias. Por exemplo, caso as categorias sejam os meses do ano, a lista deve possuir 12 elementos.
    """
    def adicionar_serie(self, nome, lista_dados):
        self.series.append((nome, simplejson.dumps(lista_dados)))
    
    """
        Formata a mensagem que é mostrada ao usuário ao posicionar o cursor do mouse sob a série.
            str: string de formatação. Deve conter dois padrões de texto. O primeiro deles está associado ao rótulo, enquanto que
            o segundo a seu valor. Ex: supondo que se deseje exibir o orçamento de cada UO nos dois semestres do ano, a string de
            formatação '{rotulo} : {valor}' será exibida ao usuário como sendo 'CNat: 3000000' caso a série em questão tenha sido
            adicionada com o nome 'CNat' e o valor do gráfico naquele ponto seja 3000000.
            Qualquer formatação HTML pode ser aplicada. Por exemplo, '<b>{rotulo}</b> : {valor}'
    """
    def formatar_dica(self, str):
        self.formatacao_tooltip = str.replace('{rotulo}', '\'+ this.x +\'').replace('{valor}', '\'+ this.y +\'')
    
    """
        Renderiza o template do gráfico de acordo com os valores de seus atributos.
        Utiliza o arquivo grafico2D.html
    """
    def __unicode__(self):
        return render_to_string('graficos/grafico2D.html', {'g' : self}) 

    
"""
    Classe concreta para a classe abstrata Grafico1D.
    O gráfico será renderizado no formato de pizza, ou seja, contendo fatias para cada dado adicionado.
""" 
class Pizza(Grafico1D):
    def __init__(self):
        self.dados = []

"""
    Classe concreta para a classe abstrata Grafico1D.
    O gráfico será renderizado no formato de rosca, ou seja, contendo fatias para cada dado adicionado.
    Esse gráfico difere do gráfico Pizza somente por apresentar uma cavidade no eixo central.
""" 
class Rosca(Grafico1D):
    def __init__(self):
        self.dados = []
        self.extra_attrs = ' innerSize: \'30%\','
                
"""
    Classe concreta para a classe abstrata Grafico2D.
    O gráfico será renderizado no formato de barra, ou seja, colunas exibidas horizontalmente.
""" 
class Barra(Grafico2D):
    def __init__(self):
        self.tipo = 'bar'
        self.series = []

"""
    Classe concreta para a classe abstrata Grafico2D.
    O gráfico será renderizado no formato de Colunas verticalmente dispostas.
"""    
class Coluna(Grafico2D):
    def __init__(self):
        self.tipo = 'column'
        self.series = []

"""
    Classe concreta para a classe abstrata Grafico2D.
    O gráfico será renderizado no formato de linhas horizontalmente dispostas.
"""     
class Linha(Grafico2D):
    def __init__(self):
        self.tipo = 'line'
        self.series = []

from datetime import timedelta
class GraficoAgendamento:
    horas = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
    def __init__(self, limite_inferior, limite_superior):
        self.items = []
        self.limite_inferior = limite_inferior
        self.limite_superior = limite_superior
        self.dias = []
        self.js =  ""
        data = limite_inferior
        while data <= limite_superior:
            self.dias.append(data.strftime('%d/%m/%Y'))
            data = data + timedelta(1)
    def get_limite_inferior_str(self):
        return self.limite_inferior.strftime('%d/%m/%Y')
    def get_limite_superior_str(self):
        return self.limite_superior.strftime('%d/%m/%Y')
    def get_tamanho_linha(self):
        return 220+(len(self.dias)*120)
    def set_items(self, items):
        for item in items:
            descricao = str(item)
            if len(descricao) > 30:
                descricao = descricao[0:25] + '...'
            self.items.append([item.id, descricao])
    def __unicode__(self):
        return render_to_string('graficos/grafico_agendamento.html', {'grafico' : self}) + SafeUnicode('<script>'+self.js+'</script>')
    def preencher_intervalo(self, item_id, cor,  data_inicio, data_fim, texto):
        dinicio = data_inicio.strftime('%d/%m/%Y')
        hinicio = data_inicio.strftime('%H:%M')
        dfim = data_fim.strftime('%d/%m/%Y')
        hfim = data_fim.strftime('%H:%M')
        self.js+="paint_div('"+cor+"', "+str(item_id)+", '"+dinicio+"', '"+hinicio+"', '"+dfim+"', '"+hfim+"', '"+texto+"');"