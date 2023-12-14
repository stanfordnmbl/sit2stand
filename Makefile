.PHONY: docker
docker:
	docker build . -t stanfordnmbl/motionlab

.PHONY: push
push:
	docker push stanfordnmbl/motionlab

.PHONY: stop
stop:
	if [ -n "$$(docker ps -q -f name=motionlab_openpose)" ]; then \
		docker kill motionlab_openpose 2> /dev/null; \
	fi
	if [ -n "$$(docker ps -aq -f name=motionlab_openpose)" ]; then \
		docker rm motionlab_openpose 2> /dev/null; \
	fi
	docker-compose down

.PHONY: start
start:
	docker-compose up -d
        # -v $(pwd)/.env:/code/.env
	docker run --name motionlab_openpose --link motionlab_redis_1:redis --link motionlab_www_1:www --net motionlab_default -d --shm-size=1g --ulimit memlock=-1 --ulimit stack=67108864 stanfordnmbl/motionlab-worker /bin/sh -c 'celery -A worker worker --loglevel=info --concurrency=1 --pool=solo'

run: docker stop start
