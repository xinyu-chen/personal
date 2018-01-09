# reporting app engine in python
Google Dataflow process for migration process of data from the following sources:


*Build base image
docker build -t python-appengine-sumo-base -f ./Dockerfile . --no-cache
docker tag [containerId] gcr.io/ordinal-ember-163410/python-appengine-sumo-base
gcloud docker -- push gcr.io/ordinal-ember-163410/python-appengine-sumo-base

*Build docker locally
docker build -t local/python -f ./Dockerfile .

to run:
docker run -it -p 8080:8080 local/python:latest

* Installation
virtualenv -p python3 env

Before running or deploying this application, install the dependencies using pip:
pip install -t lib -r requirements.txt

* Deploy
gcloud app deploy

* Running the application (need to be in app folder)
python main.py

by gunicorn:
cd app
gunicorn -b :8080 wsgi
