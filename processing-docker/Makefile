.PHONY: build
build:
	docker build -t stanfordnmbl/motionlab-worker .
.PHONY: push
push:
	docker push stanfordnmbl/motionlab-worker
.PHONY: run
run:
	docker run --env-file=.env --gpus all -it stanfordnmbl/motionlab-worker
