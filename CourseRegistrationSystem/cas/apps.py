from django.apps import AppConfig
from suit.apps import DjangoSuitConfig

class CasConfig(AppConfig):
    name = 'cas'

class SuitConfig(DjangoSuitConfig):
    layout = 'horizontal'
