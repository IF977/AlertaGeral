# -*- coding: utf-8 -*-

# O processo de permissões:
# O script deve ter opções para:
#    - Resetar todas as permissões (padrão)
#    - Somente garantir as permissões dos grupos
#    - Poder escolher a aplicação a resetar/atualizar permissões
#    - Validar se o grupo já foi definido
#    - Validar duplicidade de permissão em um mesmo grupo
#    - Colocar uma opção force para efetuar as operações indepente das Warnings

from xml.dom import minidom

def getText(nodelist):
    rc = ""
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc = rc + node.data
    return rc

class Permission:
    def __init__(self, name):
        self.setName(name)
    
    def setName(self, name):
        self.name = name
    
    def getName(self):
        return self.name

class Model:
    def __init__(self, name, app_label):
        self.setName(name)
        self.app_label = app_label
        self.permissions = []
    
    def setName(self, name):
        self.name = name
    
    def getName(self):
        return self.name
    
    def addPermission(self, permission):
        self.permissions.append(permission)
    
    def getPermissions(self):
        return self.permissions

class Group:
    def __init__(self, name=None):
        self.setName(name)
        self.models = []
    
    def setName(self, name):
        self.name = name
    
    def getName(self):
        return self.name
    
    def addModel(self, model):
        self.models.append(model)
    
    def getModels(self):
        return self.models
    
class GroupPermission:
    def __init__(self, app_name):
        self.app_name = app_name
        self.groups = []

    def setAppName(self, app_name):
        self.app_name = app_name
    
    def getAppName(self):
        return self.app_name
    
    def getGroups(self):
        return self.groups
    
    def process(self, permissionFileName):
        dom = minidom.parse(permissionFileName).documentElement
        
        # Start process permission file
        for group in dom.getElementsByTagName("group"):
            myGroup = Group(getText(group.getElementsByTagName("name")[0].childNodes))
            
            # Process permissions
            for model in group.getElementsByTagName("model"):
                myModel = Model(
                    getText(model.getElementsByTagName("name")[0].childNodes),
                    getText(model.getElementsByTagName("app")[0].childNodes),
                )

                for permission in model.getElementsByTagName("permission"):
                    myPermission = Permission(getText(permission.childNodes))
                    myModel.addPermission(myPermission)
                myGroup.addModel(myModel)
            
            self.groups.append(myGroup)
    
    def getDict(self):
        retValue = {}
        
        for group in self.groups:
            perm = []
            
            for model in group.getModels():
                for permission in model.getPermissions():
#                    if permission.getName() in ['add', 'change', 'delete']:
#                        perm.append("%s.%s.%s_%s" % (self.app_name, model.getName(), permission.getName(), model.getName()))
#                    else:
                    perm.append("%s.%s.%s" % (model.app_label, model.getName(), permission.getName()))
            retValue[group.getName()] = perm
            
        return retValue

#arquivo_permissoes = 'permissoes.xml'
#groupPermission = GroupPermission()
#groupPermission.process(arquivo_permissoes)
#
#print "-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-="
#print "Grupos"
#for group in groupPermission.getGroups():
#    print group.getName()
#    print group.getMenu()
#    for menuItem in group.getMenu().getItens():
#        print menuItem.getName()
#    for model in group.getModels():
#        print "\t", model.getName()
#        for permission in model.getPermissions():
#            print "\t\t", permission.getName()
