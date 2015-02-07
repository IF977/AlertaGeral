# -*- encoding: utf-8 -*-

"""
Inspirado em http://code.google.com/p/django-thumbs/
Melhorias:
- redimensionamento da imagem
- guarda os thumbs em pastas separadas para cada tamanho
- opção use_id_for_name
"""

from PIL import Image
from django.db.models import ImageField
from django.db.models.fields.files import ImageFieldFile
import os

class ImageWithThumbsFieldFile(ImageFieldFile):
    """
    See ImageWithThumbsField for usage example
    """
    def __init__(self, *args, **kwargs):
        super(ImageWithThumbsFieldFile, self).__init__(*args, **kwargs)
        
        if self.field.sizes:
            for size in self.field.sizes:
                setattr(self, 'url_%sx%s' % size, self.get_thumb_url(size))
    
    def get_thumb_url(self, size):
        if not self:
            return ''
        splited = list(os.path.split(self.url))
        splited.insert(-1, '%dx%d' % size)
        return os.path.join(*splited)
                
    def save(self, name, content, save=True):
        if self.field.use_id_for_name:
            extension = name.split('.')[-1]
            name = '%s.%s' % (self.instance.id, extension)
        super(ImageWithThumbsFieldFile, self).save(name, content, save)
        if self.field.sizes:
            for size in self.field.sizes:
                base_dir, photo_name = os.path.split(self.path)
                thumb_dir = os.path.join(base_dir, '%dx%d' % size)
                if not os.path.exists(thumb_dir):
                    os.mkdir(thumb_dir)
                imin = Image.open(self.path)
                width, height = imin.size
                nwidth = (height/4) * 3
                x = (width-nwidth) / 2
                if x > 0:
                    imout = imin.crop((x, 0, width-x, height)) 
                else:
                    imout = imin.crop((0, 0, width, height)) 
                imout = imout.resize(size)
                thumb_file = os.path.join(thumb_dir, photo_name)
                if os.path.exists(thumb_file):
                    os.remove(thumb_file)
                imout.save(thumb_file)
        
    def delete(self, save=True):
        name = self.name
        super(ImageWithThumbsFieldFile, self).delete(save)
        if self.field.sizes:
            for size in self.field.sizes:
                splited = list(os.path.split(name))
                splited.insert(-1, '%dx%d' % size)
                thumb_name = os.path.join(*splited)
                try:
                    self.storage.delete(thumb_name)
                except:
                    pass
                        
class ImageWithThumbsField(ImageField):
    
    attr_class = ImageWithThumbsFieldFile
    
    def __init__(self, verbose_name=None, name=None, width_field=None, height_field=None, sizes=None, **kwargs):
        self.verbose_name = verbose_name
        self.name = name
        self.width_field = width_field
        self.height_field = height_field
        self.sizes = sizes
        self.use_id_for_name = kwargs.pop('use_id_for_name', False)
        super(ImageField, self).__init__(**kwargs)
        