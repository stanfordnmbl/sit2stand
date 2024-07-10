import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as stats
from scipy.interpolate import interp1d, splrep, splev
    
from utils import *

def get_stats(keypoints_path, path, subject_id = "new"):
    keypoints = json2np(keypoints_path)

    _, file_extension = os.path.splitext(path)
    CMD = "ffprobe -v error -select_streams v -of default=noprint_wrappers=1:nokey=1 -show_entries stream=r_frame_rate /motionlab/input/input{}".format(file_extension)
    fps_str = os.popen(CMD).read().strip()

    nm,dnm = fps_str.split("/")
    fps = float(nm) / float(dnm)

    res_dict = process_subject(keypoints, subjectid = subject_id, framerate = fps, plots_path = "/motionlab/output/plots")
    nose_y = keypoints[:,[NOSE*3+1,]]

    # Smooth the curve for finding a 'better' minimum
    x = range(len(nose_y))
    f = splrep(x, nose_y, s=10**6)
    nose_y_smooth = splev(x, f)
    _, peaks = peakdet(nose_y_smooth, 10) # save positions of minima

    if len(peaks) == 0:
        # Smooth the curve for finding a 'better' minimum. This time apply lees smooth factor.
        x = range(len(nose_y))
        f = splrep(x, nose_y, s=10 ** 2)
        nose_y_smooth = splev(x, f)
        _, peaks = peakdet(nose_y_smooth, 10)  # save positions of minima

    n = peaks.shape[0]

    # TODO we can get a better estimate of breaks from multiple signals at once
    breaks = peaks[:,0].astype(np.uint16)
    breaks.sort()

    # plt.title("Peaks of the nose",fontsize=24)
    # plt.xlabel("frame",fontsize=17)
    # plt.ylabel("position",fontsize=17)
    # plt.plot(nose_y, linestyle="-", linewidth=2.5)

    # for i in range(peaks.shape[0]):
    #     plt.axvline(x=peaks[i,0],linewidth=2, color='g', linestyle="--")
    # plt.show()
        
    n = peaks.shape[0]

    first = breaks[0]
    last = breaks[-1]

    # Approximated 
    time = n*(last-first)/((n-1)*fps)

    lkneeangle = get_angle(LANK, LKNE, LHIP, keypoints)

    s2s_times = (breaks[1:] - breaks[:-1])/fps
    # bstats = plt.boxplot(s2s_times)

    plt.figure()
    for i in range(len(breaks)-1):
        num_points = breaks[i + 1] - breaks[i]
        if num_points <= 3:
            # Skip this segment if there are not enough points
            continue
        x = np.linspace(0, 1, num=breaks[i+1] - breaks[i], endpoint=True)
        y = np.pi - lkneeangle[breaks[i]:breaks[i+1]]
        f = splrep(x, y, s=0.03)
        xplot = np.linspace(0, 1, num=breaks[i+1] - breaks[i], endpoint=True)
        plt.plot(xplot*100, 180*splev(xplot, f)/np.pi)

    plt.xlabel("% of the cycle",fontsize=17)
    plt.ylabel("angle",fontsize=17)
    plt.title("L knee flex of sit-to-stands",fontsize=24)
    plt.savefig("/motionlab/output/plots/knee-flex-curves.png")

    consistency = 1 - s2s_times.std() / s2s_times.mean()

    res_dict.update({
        "consistency": consistency,
    })
    return res_dict
