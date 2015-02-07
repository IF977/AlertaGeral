# -*- coding: utf-8 -*-

""" Test the db module """

from django.test import TestCase
from djtools.db import get_connection, is_null_column, table_exists, \
                        sequence_is_owned_by, get_dict_dict

class FunctionsTest(TestCase):

    def setUp(self):
        self.connection = get_connection(conn=None)
        
        sql = """ CREATE TABLE test
                (
                  id serial NOT NULL,
                  nome character varying(40)
                );
                """
        cur = self.connection.cursor()
        cur.execute(sql)
     
    def tearDown(self):
        pass

    def test_table_exists(self):
        """ table_exists function should return True if table exists, False otherwise """
        self.assertTrue(table_exists('test', conn=None))
        self.assertFalse(table_exists('testxxx', conn=None))
        
    def test_is_null_column(self):
        """ is_null_column should return True if column allows null values, False otherwise """
        self.assertFalse(is_null_column('test', 'id', conn=None))
        self.assertTrue(is_null_column('test', 'nome', conn=None))
    
    def test_sequence_is_owned_by(self):
        # Essa teste deveria estar mais completo, por exemplo fazendo algumas
        # manipulações no sequence, mas não consegui alterar o owner para outro campo
        # nem para NONE
        self.assertTrue(sequence_is_owned_by('test_id_seq', 'test.id'))
        self.assertFalse(sequence_is_owned_by('test_id_seq', 'test.nome'))
    
    def test_get_dict_dict(self):
        """  get_dict_dict should  return a dict of dict
             Ex:
            >>> sql = ''SELECT field1, field2 FROM table'
            >>> get_dict_dict(sql, field1) 
            {'key1': {'field1': 'key1', 'field2': 'value'},
             'key2': {'field1': 'key2', 'field2': 'value'}}
        """
        sql = """ INSERT INTO test(id, nome) \
                    VALUES (1, 'nome1'); \
                  INSERT INTO test(id, nome) \
                    VALUES (2, 'nome2');
                """
        cur = self.connection.cursor()
        cur.execute(sql)
        
        sql = 'SELECT id, nome FROM test'
        r = {1:{'id':1, 'nome': 'nome1'},
             2:{'id':2, 'nome': 'nome2'}}
        self.assertEqual(get_dict_dict(sql, 'id'), r)
        
