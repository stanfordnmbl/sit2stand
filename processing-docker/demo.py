import pandas as pd
import numpy as np
import os
import json
import os.path
from analysis import get_stats
import traceback

def run_openpose(path):

    CMD = "ffprobe -loglevel error -select_streams v:0 -show_entries stream_tags=rotate -of default=nw=1:nk=1 -i {}".format(path)
    rotate = os.popen(CMD).read().strip()

    if rotate:
        _, file_extension = os.path.splitext(path)
        path_tmp = "/motionlab/input/tmp{}".format(file_extension)
        os.system("mv {} {}".format(path, path_tmp))
        
        path = "/motionlab/input/input.mp4"
        CMD = "ffmpeg -y -i {} {}".format(path_tmp, path)
        
        print(CMD)
        os.system(CMD)

    os.system('rm /motionlab/output/* -r; mkdir /motionlab/output/plots ; cd /openpose ; /openpose/build/examples/openpose/openpose.bin --video {} --display 0 --write_json /motionlab/output/keypoints -write_video /motionlab/output/output.mp4 ; cd /motionlab'.format(path))

def zip_everything():
    os.system("cd /motionlab ; tar -czvf output.tar.gz output ; mv /motionlab/output.tar.gz /motionlab/output/")

def predict(path, subjectid = "new"):
    run_openpose(path)

    stats = {}
    try:
        stats = get_stats("/motionlab/output/keypoints", subject_id = subjectid)
    except Exception as e:
        print(e)
        traceback.print_exc()
        pass

    zip_everything()

    print(stats)

    return stats, open("/motionlab/output/output.tar.gz", "rb")

if __name__ == "__main__":

    predict("/motionlab/input/input.mp4")
    #predict("/motionlab/input/input.MOV")
    
    # Saves video to "/motionlab/output/output.mp4"
    # Saves keypoints to "/motionlab/output/keypoints/"
