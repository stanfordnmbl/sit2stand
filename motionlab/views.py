from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from motionlab.forms import VideoForm
from django.forms.widgets import ClearableFileInput
from django.shortcuts import render, redirect
from motionlab.models import Video, Annotation
from motionlab import celery_app
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail, BadHeaderError
import json
import os
import boto3
import math
from decouple import config
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from django.views.decorators.csrf import csrf_exempt

from .forms import ContactForm, ApplicationForm

key_mapping = {
    "time": "Time",
    "consistency": "Consistency",
    "n": "Num of repetitions",
}

def consistency(x):
    x = float(x)
    if math.isnan(x):
        x = 0
    x = int(x  * 100)
    return "{}%".format(x)

transform = {
    "n": lambda x: int(float(x)),
    "consistency": consistency,
    "time": lambda x: "{:.2f}s".format(float(x)),
}

def update_results(results):
    keys = set(key_mapping.keys()) & set(results.keys())
    return { key_mapping[key]: transform.get(key, lambda x:x)(results[key]) for key in keys }

def rerun_all(request):
    annos = Annotation.objects.all().order_by("id")
    for anno in annos:
        celery_app.send_task("motionlab.sitstand", ({
            "annotation_id": anno.id,
            "video_url": anno.video.file.url,
            "subject_id": anno.video.slug
        }, ))

def analysis_json(request, slug):
    annotation = Annotation.objects.get(video__slug=slug)
    response = HttpResponse(json.dumps(annotation.response, indent=4, sort_keys=True), content_type="application/json")
    response['Content-Disposition'] = f'attachment; filename={slug}.json'
    return response

def analysis(request, slug):
    video = Video.objects.get(slug=slug)

    videos = Video.objects.all().order_by("id")
    example_slug = "0eHy4fTr"
#    if videos.count()>0:
#        example_slug = videos[0].slug

    if video.annotation_set.count() == 0:
        ann = Annotation(video=video)
        ann.save()
        celery_app.send_task("motionlab.sitstand", ({
            "annotation_id": ann.id,
            "video_url": video.file.url,
            "subject_id": video.slug
        }, ))

    annotations = video.annotation_set.all()
    annotation = None
    if annotations.count() > 0:
        annotation = annotations[0]

    # convert to int
    results = annotation.response

    if results:
        results = update_results(results)
    return render(request, 'motionlab/analysis.html', {
        "video": video,
        "annotation": annotation,
        "results": results,
        "is_example": example_slug == slug,
    })

def index(request):
    videos = Video.objects.all().order_by("id")
    example_slug = "0eHy4fTr"
    # if videos.count()>0:
    #     example_slug = videos[0].slug

    return render(request, 'motionlab/index.html', {
        "example_slug": example_slug,
    })
    
def consent(request):
    return render(request, 'motionlab/consent.html')

def thankyou(request, mode):
    msg = "Thank you for your interest in this study. At this time, your responses do not qualify you to participate. If you agreed to be contacted in the future, we may contact you with future opportunities."

    if mode != 'default':
        msg = "We’re sorry, but we require another person to be present to make sure you are safe during your participation. Please come back when another person is present!"
        
    return render(request, 'motionlab/thankyou.html', {
        "msg": msg,
    })

def aboutus(request):
    return render(request, 'motionlab/aboutus.html')

def terms(request):
    return render(request, 'motionlab/terms.html')

def beforestart(request):
    return render(request, 'motionlab/beforestart.html', {"private": request.session.get("private", False)})

QUESTIONS = [
    ("Do you currently reside in the United States?",True),
    ("Are you over 40 years old?",True),
    ("Have you gotten up from a chair unassisted within the past week?",True),
    ("Do you feel safe sitting down on and standing up from a chair without the use of your arms?",True),
    ("Are you with another person who can monitor your participation and record your video?",True),
    ("Has your doctor ever said that you have a heart condition and that you should only do physical activity recommended by a doctor?",False),
    ("Do you feel pain in your chest when you do physical activity?",False),
    ("In the past month, have you had chest pain when you were not doing physical activity?",False),
    ("Do you lose your balance because of dizziness or do you ever lose consciousness?",False),
    ("Do you have a bone or joint problem that could be made worse by performing the movement of standing up from a chair?",False),
    ("Is your doctor currently prescribing drugs for your blood pressure or heart condition?",False),
    ("Do you know of any other reason why you should not do physical activity?",False),
]


def private(request):
    request.session["private"] = True
    return redirect("beforestart")

def reset(request):
    request.session["private"] = False
    return redirect("index")

def readiness(request, page):
    if "recordid" in request.GET:
        request.session["recordid"] = request.GET["recordid"]
    
    if page == len(QUESTIONS)+1:
        return redirect("form")

    thankyoumode = "default"
    if page == 5:
        thankyoumode = "otherperson"

    # TODO: That's a very hacky way to handle blood pressure question
    # IF the logic in readiness gets more complicated this should be removed
    hackmode = False
    if page != 100:
        question = QUESTIONS[page-1][0]
        answer = QUESTIONS[page-1][1]
    else:
        page = 11
        question = "Has your doctor confirmed that it is safe for you to be physically active while on your blood pressure medication?"
        answer = True
        hackmode = True
        
    return render(request, 'motionlab/readiness.html', {
        "current": page,
        "all": len(QUESTIONS),
        "next": page + 1,
        "question": question,
        "answer": answer,
        "thankyoumode": thankyoumode,
        "hackmode": hackmode,
    })

@csrf_exempt
def form(request):
    if request.method == 'POST':
        form = VideoForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save()
            ann = Annotation(video=obj)
            ann.save()
            celery_app.send_task("motionlab.sitstand", ({
                "annotation_id": ann.id,
                "video_url": obj.file.url,
                "subject_id": obj.slug,
            }, ))
            return redirect("validate", obj.slug)
    else:
        form = VideoForm(initial={'recordid': -1})
        
    form.fields["file"].widget.attrs['accept'] = 'video/*;capture=camera'

    return render(request, 'motionlab/form.html', {
        "form": form,
        # "recordid": request.session["recordid"]
    })

def validate(request, slug):
    video = Video.objects.get(slug=slug)

    return render(request, 'motionlab/validate.html', {
        "video": video,
    })

def uploadDirectory(source_path, target_path, bucketname):
    s3_client = boto3.client('s3')
    for root, dirs, files in os.walk(source_path):
        for file in files:
            s3_client.upload_file(os.path.join(root,file),
                                  bucketname,
                                  "{}/{}".format(target_path, file),
                                  ExtraArgs={
                                      'ContentType': 'image/png',
                                      'ACL':'public-read'
                                  })
@csrf_exempt
def annotation_update(request, id):
    ann = Annotation.objects.get(id=id)

    os.system("rm /tmp/output -r")

    filename = "/tmp/{}.tar.gz".format(id)

    with open(filename, 'wb+') as destination:
        for chunk in request.FILES["file"].chunks():
            destination.write(chunk)

    os.system("tar -zxvf {} -C /tmp/".format(filename))
    
    ann.file.save("output.mp4", open("/tmp/output/output.mp4","rb"))
    uploadDirectory("/tmp/output/plots","media/outputs/{}/plots".format(ann.video.slug),"mc-motionlab-storage")
    uploadDirectory("/tmp/output/keypoints","media/outputs/{}/keypoints".format(ann.video.slug),"mc-motionlab-storage")

    s3_client = boto3.client('s3')
    s3_client.upload_file(filename,
                          "mc-motionlab-storage",
                          "media/outputs/{}/output.tar.gz".format(ann.video.slug),
                          ExtraArgs={
                              'ContentType': 'application/tar+gzip',
                              'ACL':'public-read'
                          })

    # Save "/tmp/output/plots" directory to "/media/output/{videoid}/plots"
        
    print(request.POST["result"])
    ann.response = json.loads(request.POST["result"])
    if len(ann.response.keys()) > 0:
        ann.status = "done"
    else:
        ann.status = "error"
    ann.save()
    return HttpResponse("Done")

def contact(request):
    if request.method == 'GET':
        form = ContactForm()
    else:
        form = ContactForm(request.POST)
        if form.is_valid():
            message = Mail(
                from_email='Sit2Stand User <sit2stand.ai@gmail.com>',
                to_emails=['sit2stand.ai@gmail.com','lukasz.kidzinski@gmail.com'],
                subject=form.cleaned_data['subject'],
                html_content=form.cleaned_data['message'])
            message.reply_to = form.cleaned_data['your_email']
            sg = SendGridAPIClient(config('SENDGRID_API_KEY'))
            response = sg.send(message)
            print(response.status_code)
            body = "E-mail: {}\n\n{}".format(form.cleaned_data['your_email'], response.body)
            print(body)
            print(response.headers)
            return redirect('success')
    return render(request, "motionlab/contact.html", {'form': form})

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def application(request):
    if request.method == 'GET':
        form = ApplicationForm()
    else:
        form = ApplicationForm(request.POST)
        if form.is_valid():
            sg = SendGridAPIClient(config('SENDGRID_API_KEY'))
            body = "Name: {}<br/>E-mail: {}<br/>State: {}<br/>IP: {}<br/>\nHow you learned:<br/>{}".format(
                form.cleaned_data['your_name'],
                form.cleaned_data['your_email'],
                form.cleaned_data['your_state'],
                get_client_ip(request),
                form.cleaned_data['how'])
            message = Mail(
                from_email='Sit2Stand User <sit2stand.ai@gmail.com>',
                to_emails=['sit2stand.ai@gmail.com','lukasz.kidzinski@gmail.com'],
                subject="Application: " + form.cleaned_data['your_name'],
                html_content=body)
            message.reply_to = form.cleaned_data['your_email']
            response = sg.send(message)
            print(response.status_code)
            print(response.headers)
            return redirect('success')
    return render(request, "motionlab/application.html", {'form': form})

def success(request):
    return HttpResponse('Success! Thank you for your message.')
