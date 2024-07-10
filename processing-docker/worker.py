from celery import Celery
from demo import predict, zip_everything
import urllib.request
import shutil
import os
import requests
import json
from decouple import config
import traceback

app = Celery('motionlab', broker='redis://default:{}@34.222.100.180:6379/0'.format(config("REDIS_PASS")))

@app.task(name='motionlab.sitstand')
def cp(args):
    try:
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
                          data = {"status": "success", "error_messsage": "", "result": json.dumps(result)})
        print(r.text)

        return {"status": "success", "message": "Video analyzed successfully."}

    except Exception as e:
        # Try to zip results generated until error.
        file = None
        try:
            zip_everything()
            file = open("/motionlab/output/output.tar.gz", "rb")
        except Exception as e2:
            print(str(e))
            print(traceback.format_exc())


        # Annotate empty, so it is registered as error.
        r = requests.post("https://sit2stand.ai/annotation/{}/".format(args["annotation_id"]),
                          files = {'file': file},
                          data = {"status": "error", "error_messsage": str(e), "result": ""})
        print(r.text)

        return {"status": "error", "message": str(e)}

