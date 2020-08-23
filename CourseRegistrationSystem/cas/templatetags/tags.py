from django.template.defaulttags import register

from django import template

register = template.Library()
@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def get_name(dictionary, key):
    return get_item(dictionary, key).name

@register.filter
def get_teacher(dictionary, key):
    return get_item(dictionary, key).teacher

@register.filter
def get_section(dictionary, key):
    return get_item(dictionary, key).section

@register.filter
def get_time(dictionary, key):
    return get_item(dictionary, key).time

@register.filter
def get_position(dictionary, key):
    return get_item(dictionary, key).position