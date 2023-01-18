from celery import Celery
from demo import predict
import urllib.request
import shutil
import os
import requests
import json
from decouple import config

app = Celery('motionlab', broker='redis://default:{}@34.222.100.180:6379/0'.format(config("REDIS_PASS")))

@app.task(name='motionlab.sitstand')
def cp(args):
    # save the new file
    url = args["video_url"]
    _, file_extension = os.path.splitext(url)

    os.makedirs("/motionlab/input/",exist_ok=True)
    os.makedirs("/motionlab/output/",exist_ok=True)
    
    path = "/motionlab/input/input{}".format(file_extension)

    if os.path.exists(path):
        os.remove(path)
    else:
        print("The file {} does not exist".format(path)) 

    with urllib.request.urlopen(url) as response, open(path, 'wb') as out_file:
        shutil.copyfileobj(response, out_file)

    # run predictions
    print(args)
    result, video = predict(path, args["subject_id"])

    files = {'file': video}

    # store results
    r = requests.post("https://sit2stand.ai/annotation/{}/".format(args["annotation_id"]),
                      files = files,
                      data = {"result": json.dumps(result)})
    print(r.text)

    return None
