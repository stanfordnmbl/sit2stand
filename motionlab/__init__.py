from __future__ import absolute_import, unicode_literals

# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from .celery import app as celery_app

__all__ = ('celery_app',)

# app/__init__.py
from django.template.defaultfilters import register

# Import your custom filter
from motionlab.templatetags.custom_filters import get_slugs, index, num_processed, get_json_value

# Register the custom filter
register.filter('get_slugs', get_slugs)
# Register the custom filter
register.filter('index', index)
# Register the custom filter
register.filter('num_processed', num_processed)
# Register the custom filter
register.filter('get_json_value', get_json_value)

