from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from motionlab.forms import VideoForm, MultipleVideosForm
from django.forms.widgets import ClearableFileInput
from django.shortcuts import render, redirect
from motionlab.models import Video, Annotation
from motionlab import celery_app
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail, BadHeaderError
import json
import csv
import os
import boto3
import math
from decouple import config
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from django.views.decorators.csrf import csrf_exempt
from django.core import serializers
import re
import logging
import urllib.parse

from .forms import ContactForm, ApplicationForm

key_mapping = {
    "trunk_lean_max": "Trunk flexion",
    "trunk_lean_max_ang_acc": "Trunk acceleration"
}

unit_mapping = {
    "Trunk flexion": "degrees",
    "Trunk acceleration": "degrees/s²",
    "Total time": "s"
}

def remove_uuid_from_filename(file_name):
    # Regex pattern for UUID
    uuid_pattern = re.compile(r'-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.')

    # Use regex to find and replace UUID with an empty string
    file_name_without_uuid = re.sub(uuid_pattern, '.', file_name)

    return file_name_without_uuid

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


def analysis_csv(request, slug):
    # Get annotations from database.
    annotation = Annotation.objects.get(video__slug=slug)
    # Get data as json.
    json_data = annotation.response
    # Convert json into csv.
    csv_data = ""
    # Get file name and add it at start.
    video_name = remove_uuid_from_filename(annotation.video.file.name.replace("inputs/", ""))
    # Remove extension.
    video_name = video_name.split('.')[0]

    # Add to csv.
    csv_data += "filename" + ", " + video_name + "\n"
    if json_data and len(json_data) != 0:
        for attribute, value in json_data.items():
            csv_data += attribute + ", " + str(value) + "\n"

    # Generate and return response object.
    response = HttpResponse(csv_data, content_type="text/csv")
    response['Content-Disposition'] = f'attachment; filename={video_name}.csv'

    return response

def analysis_simple_csv(request, slug):
    # Get annotations from database.
    annotation = Annotation.objects.get(video__slug=slug)
    # Get data as json.
    json_data = annotation.response
    print("JSON DATA: " + str(annotation))
    # Convert json into csv.
    csv_data = ""
    # Get file name.
    video_name = remove_uuid_from_filename(annotation.video.file.name.replace("inputs/", ""))
    # Remove extension.
    video_name = video_name.split('.')[0]


    # Add data to csv.
    if json_data and len(json_data) != 0:
        csv_data += "filename" + ", " + video_name + "\n"
        csv_data += "Total Time" + ", " + str(((json_data["time"] / json_data["n"]) * 5)) + "\n"
        csv_data += "Trunk flexion" + ", " + str(json_data["trunk_lean_max"] - 180) + "\n"
        csv_data += "Trunk acceleration" + ", " + str(json_data["trunk_lean_max_ang_acc"]) + "\n"

    # Generate and return response object.
    response = HttpResponse(csv_data, content_type="text/csv")
    response['Content-Disposition'] = f'attachment; filename=simple_{video_name}.csv'

    return response

def analysis(request, slug):
    video = Video.objects.get(slug=slug)

    # Get video_name.
    video_name = remove_uuid_from_filename(video.file.name.replace("inputs/", "").replace(".mp4", ""))
    video_name = video_name.split('.')[0]

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

    results = annotation.response

    if results and "error_messsage" not in results:
        # Calculate total time.
        total_time = (results["time"] / results["n"]) * 5

        results = update_results(results)
        # Add total time.
        results["Total time"] = total_time

        # Format and add units.
        for key, label in results.items():
            if key == "Trunk flexion":
                results[key] = str(round(label - 180, 1)) + " " + unit_mapping[key]
            elif key == "Trunk acceleration":
                results[key] = str(int(round(label, 0))) + " " + unit_mapping[key]
            else:
                results[key] = str(round(label, 1)) + " " + unit_mapping[key]

        # Sort elements.
        results = dict(sorted(results.items()))

    return render(request, 'motionlab/analysis.html', {
        "video": video,
        "video_name": video_name,
        "annotation": annotation,
        "results": results,
        "is_example": example_slug == slug,
    })

def analysis_multiple(request, slugs):

    video_slugs = []
    annotation_file_urls = {}
    video_file_urls = {}
    annotation_statuses = {}
    results_list = {}
    video_names = []
    error_messages = {}

    for slug in slugs:
        video = Video.objects.get(slug=slug)

        # Get annotations.
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

        results = annotation.response

        if results and "error_messsage" not in results:
            # Calculate total time.
            total_time = (results["time"] / results["n"]) * 5

            results = update_results(results)
            # Add total time.
            results["Total time"] = total_time

            # Format and add units.
            for key, label in results.items():
                if key == "Trunk flexion":
                    results[key] = str(round(label - 180, 1)) + " " + unit_mapping[key]
                elif key == "Trunk acceleration":
                    results[key] = str(int(round(label, 0))) + " " + unit_mapping[key]
                else:
                    results[key] = str(round(label, 1)) + " " + unit_mapping[key]


            # Sort elements.
            results = dict(sorted(results.items()))
            results_list[video.slug] = results

        video_slugs.append(video.slug)
        video_file_urls[video.slug] = video.file.url

        # Get video_name.
        video_name = remove_uuid_from_filename(video.file.name.replace("inputs/", ""))

        video_names.append(video_name)

        if annotation.file:
            annotation_file_urls[video.slug] = annotation.file.url
        else:
            annotation_file_urls[video.slug] = None

        annotation_statuses[video.slug] = annotation.status
        results_list[video.slug] = results



    return render(request, 'motionlab/analysis_multiple.html', {
        "video_slugs": video_slugs,
        "video_names": video_names,
        "video_file_urls": json.dumps(video_file_urls),
        "annotation_file_urls": json.dumps(annotation_file_urls),
        "annotation_statuses": json.dumps(annotation_statuses),
        "results_list": json.dumps(results_list),
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

def faq(request):
    return render(request, 'motionlab/faq.html')

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
def self_assess(request):
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
            },))
            return redirect("validate", obj.slug)
    else:
        form = VideoForm(initial={'recordid': -1})

    form.fields["file"].widget.attrs['accept'] = 'video/*;capture=camera'

    return render(request, 'motionlab/self_assess.html', {
        "form": form,
        # "recordid": request.session["recordid"]
    })

@csrf_exempt
def under_construction(request):
    return render(request, 'motionlab/under_construction.html')

@csrf_exempt
def for_researchers(request):
    if request.method == 'POST':
        form = MultipleVideosForm(request.POST, request.FILES)
        if form.is_valid():
            files = request.FILES.getlist('file')  # Get a list of uploaded files
            slugs = []
            for file in files:
                obj = Video(file=file, recordid=form.cleaned_data['recordid'])
                obj.save()
                ann = Annotation(video=obj)
                ann.save()
                slugs.append(obj.slug)
                celery_app.send_task("motionlab.sitstand", ({
                    "annotation_id": ann.id,
                    "video_url": obj.file.url,
                    "subject_id": obj.slug,
                },))
            return redirect("validate_multiple", slugs)
    else:
        form = MultipleVideosForm(initial={'recordid': -1})

    form.fields["file"].widget.attrs['accept'] = 'video/*;capture=camera'
    form.fields["file"].widget.attrs['multiple'] = True  # Allow multiple file selection

    return render(request, 'motionlab/for_researchers.html', {
        "form": form,
    })


@csrf_exempt
def assess(request):
    form = VideoForm(initial={'recordid': -1})

    form.fields["file"].widget.attrs['accept'] = 'video/*;capture=camera'

    return render(request, 'motionlab/assess.html', {
        "form": form,
        # "recordid": request.session["recordid"]
    })


def validate(request, slug):
    video = Video.objects.get(slug=slug)

    return render(request, 'motionlab/validate.html', {
        "video": video,
    })

def validate_multiple(request, slugs):
    videos = []
    for slug in slugs:
        video = Video.objects.get(slug=slug)
        videos.append(video)

    return render(request, 'motionlab/validate_multiple.html', {
        'videos': videos
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

    if "file" in request.FILES:
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

    if request.POST.get("status") == "error":
        ann.status = "error"
        if "error_messsage" in request.POST:
            ann.response = json.loads('{"error_messsage" : "' + request.POST.get("error_messsage") + '"}')
    else:
        ann.status = "done"
        if request.POST.get("result") != "":
            ann.response = json.loads(request.POST.get("result"))
        else:
            ann.status = "error"
            ann.response = json.loads('{"error_messsage" : "Results field for annotation is empty."}')
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
                to_emails=['sit2stand.ai@gmail.com','lukasz.kidzinski@gmail.com', 'mboswell229@gmail.com'],
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
