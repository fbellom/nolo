APPLICATION_NAME ?= nolo-app-backend
APP_NAME = nolo_

build:
		docker build --tag ${APPLICATION_NAME} . 

docker_run:
		docker run --rm -it -p 8000:8000 --env-file env-file ${APPLICATION_NAME} --name {}

