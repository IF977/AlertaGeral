# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.db import models
from django.template import Context, Template

class Command(BaseCommand):
    
    TEMPLATE = '''<groups>
    <group>
        <name>GroupName</name>
        <models>{% for model_name in model_names %}
            <model>
                <app>{{ app_label }}</app>
                <name>{{ model_name }}</name>
                <permissions>
                    <permission>add_{{ model_name }}</permission>
                    <permission>change_{{ model_name }}</permission>
                    <permission>edit_{{ model_name }}</permission>
                    <permission>delete_{{ model_name }}</permission>                        
                </permissions>
            </model>{% endfor %}
        </models>
    </group>
</groups>'''

    def handle(self, *args, **options):
        t = Template(Command.TEMPLATE)
        app_label = args[0]
        model_names =[]
        for model_cls in models.get_models(models.get_app(app_label)):
            model_names.append(model_cls.__name__.lower())
        c = Context(dict(app_label=app_label, model_names=model_names))
        print t.render(c)
