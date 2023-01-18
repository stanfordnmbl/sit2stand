from django.contrib import admin
from motionlab.models import Video, Annotation

class AnnotationAdmin(admin.ModelAdmin):
    list_display = ('video', 'file', 'status')

class VideoAdmin(admin.ModelAdmin):
    readonly_fields = ["slug",]
    fields = ["slug","recordid","file","email",]
    list_display = ('pk','recordid', 'slug', 'file', 'email')

admin.site.register(Annotation, AnnotationAdmin)
admin.site.register(Video, VideoAdmin)
