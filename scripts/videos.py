from motionlab.models import Video
for video in Video.objects.all():
    print("{},{}".format(video.slug, video.file.url))
