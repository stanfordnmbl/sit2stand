FROM cwaffles/openpose
WORKDIR /motionlab
RUN apt update ; pip3 install --upgrade pip
RUN apt install ffmpeg python3-setuptools -y
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY . /motionlab
CMD celery -A worker --pool=solo worker