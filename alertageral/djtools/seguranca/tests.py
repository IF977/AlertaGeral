# -*- coding: utf-8 -*-
import unittest
from djtools.seguranca.xmlsec import ArquivoXMLSec, CertificadorXML, CertificadorBD, Cifrador

#Os comandos para geração das chaves e do certificado podem ser obtidos
#na URL http://acs.lbl.gov/~ksb/Scratch/openssl.html
dir_cert = '/Users/breno/Ifrn/assinatura-digital/pki/'
file = '/Users/breno/Desktop/file.rf.rtf'
xmlfile = '/Users/breno/Desktop/file.txt.xml' 

class TestXML(unittest.TestCase):
    def test_all(self):    
        return
        m = ArquivoXMLSec(xmlfile)
        m.incorporar(file, remover=False)
    
        c = CertificadorXML()
        c.assinar(dir_cert+'ksb_priv_key.pem', '12345', xmlfile)
        print c.verificar(dir_cert+'ksb_pub_key.pem', xmlfile)
        print c.verificar_com_certificado(dir_cert+'ksb_cert.pem', xmlfile)
        print c.verificar_com_certificado('/home/breno/Desktop/suap.pem', xmlfile)
        #m.extrair(file)

class TestBD(unittest.TestCase):
    def test_all(self):
        c = CertificadorBD()
        assinatura =  c.calcular_assinatura(dir_cert+'ksb_priv_key.pem', '12345', file)
        verificacao = c.verificar_com_certificado(dir_cert+'ksb_cert.pem', assinatura, file)
        print verificacao
        
        assinatura =  c.calcular_assinatura(dir_cert+'ksb_priv_key.pem', '12345', file)
        verificacao = c.verificar(dir_cert+'ksb_pub_key.pem', assinatura, file)
        print verificacao
    
class TestCifrador(unittest.TestCase):
    def test_all(self):    
        return
        cifrador = Cifrador()
        cifrador.encriptar('/home/breno/Desktop/file.rf.rtf', 'senha')
        cifrador.decriptar('/home/breno/Desktop/file.rf.rtf', 'senha')
    

suite = unittest.TestSuite()
#suite.addTest(unittest.makeSuite(TestXML))
suite.addTest(unittest.makeSuite(TestBD))
