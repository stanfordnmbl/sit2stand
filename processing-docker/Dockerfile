FROM 660440363484.dkr.ecr.us-west-2.amazonaws.com/opencap/openpose
# cwaffles/openpose
WORKDIR /motionlab
RUN apt update ; pip3 install --upgrade pip
RUN apt install ffmpeg python3-setuptools nginx -y
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY . /motionlab
CMD nginx ; celery -A worker --pool=solo worker