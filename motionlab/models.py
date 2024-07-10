from django.db import models
import jsonfield
from randomslugfield import RandomSlugField
from django.urls import reverse

import uuid
import os

def get_file_path(directory):
    def func(instance, filename):
        ext = filename.split('.')[-1]
        name = os.path.basename(filename).split('.')[0]
        name = name.replace(' ', '_')
        filename = "%s-%s.%s" % (name, uuid.uuid4(), ext)
        return os.path.join(directory, filename)
    return func

STATUS_CHOICES = [
    ("submitted","Submitted"),
    ("processing","Processing"),
    ("done","Done"),
    ("error","Error"),
]

class Video(models.Model):
    slug = RandomSlugField(length=8)
    file = models.FileField("Video file", upload_to=get_file_path("inputs"))
    email = models.EmailField(null=True)
    recordid = models.CharField(null=False, max_length=32)

    def get_absolute_url(self):
        return reverse('analysis', args=[str(self.slug)])

    def __str__(self):
        return self.slug.__str__()

class Annotation(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    file = models.FileField(upload_to=get_file_path("outputs"),
                            null=True)
    response = jsonfield.JSONField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='submitted')
