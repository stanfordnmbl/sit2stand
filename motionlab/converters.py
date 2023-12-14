from django.urls import converters

class SlugsConverter:
    regex = r'[-\w]+(?:,[-\w]+)*'

    def to_python(self, value):
        return value.split(',')

    def to_url(self, value):
        return ','.join(value)