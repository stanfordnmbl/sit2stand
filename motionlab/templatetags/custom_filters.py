from django import template
import urllib.parse
import json

register = template.Library()


@register.filter
def get_slugs(videos):
    slugs = []
    for video in videos:
        slugs.append(video.slug)
    return slugs


@register.filter
def index(indexable, i):
    try:
        return indexable[i]
    except (IndexError, TypeError):
        return ""


@register.filter(name='get_json_value')
def get_json_value(dictionary, key):
    dictionary = json.loads(dictionary)
    return dictionary.get(key, "")

@register.filter
def num_processed(annotation_statuses):
    statuses = json.loads(annotation_statuses)
    num_processed = 0
    for key, value in statuses.items():
        if value == "done" or value == "error":
            num_processed = num_processed + 1
    return num_processed

@register.filter(name='zip')
def zip_lists(a, b):
    return zip(a, b)

@register.filter
def split(value, arg):
    return value.split(arg)

@register.filter
def unquote_error(value):
    return urllib.parse.unquote(value)
