from motionlab.models import Annotation
from motionlab import celery_app

for ann in Annotation.objects.all():
    if ann.status != "done":
        celery_app.send_task("motionlab.sitstand", ({ "annotation_id": ann.id, "video_url": ann.video.file.url }, ))
