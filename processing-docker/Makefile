.PHONY: build
build:
	docker build -t stanfordnmbl/motionlab-worker .
.PHONY: push
push:
	docker push stanfordnmbl/motionlab-worker
.PHONY: run
run:
	docker run --name sit2stand-worker -p 8000:80 --env-file=.env --gpus all -d stanfordnmbl/motionlab-worker
