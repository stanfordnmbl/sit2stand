import os
import os.path
from analysis import get_stats
import traceback
import urllib.parse

def error_string(ex: Exception) -> str:
    return urllib.parse.quote('\n'.join([
        ''.join(traceback.format_exception_only(None, ex)).strip(),
        ''.join(traceback.format_exception(None, ex, ex.__traceback__)).strip()
    ]))


def run_openpose(path):

    CMD = "ffprobe -loglevel error -select_streams v:0 -show_entries stream_tags=rotate -of default=nw=1:nk=1 -i {}".format(path)
    rotate = os.popen(CMD).read().strip()

    if rotate:
        _, file_extension = os.path.splitext(path)
        path_tmp = "/motionlab/input/tmp{}".format(file_extension)
        os.system("mv {} {}".format(path, path_tmp))
        
        path = "/motionlab/input/input.mp4"
        CMD = "ffmpeg -y -i {} {}".format(path_tmp, path)

        os.system(CMD)

    os.system('rm /motionlab/output/* -r; mkdir /motionlab/output/plots ; cd /openpose ; /openpose/build/examples/openpose/openpose.bin --video {} --display 0 --write_json /motionlab/output/keypoints -write_video /motionlab/output/output.mp4 ; cd /motionlab'.format(path))


def zip_everything():
    os.system("cd /motionlab ; tar -czvf output.tar.gz output ; mv /motionlab/output.tar.gz /motionlab/output/")


def predict(path, subjectid = "new"):
    try:
        run_openpose(path)
    except Exception as e:
        print(str(e))
        print(traceback.format_exc())
        raise Exception("Error while detecting poses in your video with OpenPose: " + error_string(e))

    try:
        stats = {}
        stats = get_stats("/motionlab/output/keypoints", path, subject_id = subjectid)
    except Exception as e:
        print(str(e))
        print(traceback.format_exc())
        raise Exception("Error while calculating results from extracted poses: " + error_string(e))

    try:
        zip_everything()
    except Exception as e:
        print(str(e))
        print(traceback.format_exc())
        raise Exception("Error while zipping results: " + error_string(e))

    print(stats)

    return stats, open("/motionlab/output/output.tar.gz", "rb")


if __name__ == "__main__":

    predict("/motionlab/input/input.mp4")
    #predict("/motionlab/input/input.MOV")
    
    # Saves video to "/motionlab/output/output.mp4"
    # Saves keypoints to "/motionlab/output/keypoints/"
