FROM gcr.io/ordinal-ember-163410/python-appengine-sumo-base
LABEL python_version=python3
VOLUME /tmp

VOLUME /tmp
#ADD /app/ /app

ENV SUMOLOGIC_BASEDIR /opt/SumoCollector
ENV SUMOLOGIC_CONFDIR ${SUMOLOGIC_BASEDIR}/config
ADD ./sumologic_sources.json ${SUMOLOGIC_CONFDIR}/sumologic_sources.json

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# INSTALL gcp credentials
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
RUN mkdir -p /opt/behalf/cto/reporting/log

ENV DOCKER_BASEDIR /opt/docker
ENV DOCKER_LOGDIR  ${DOCKER_BASEDIR}/log
ENV DOCKER_SCRIPTS_DIR  ${DOCKER_BASEDIR}/scripts


# Add the application source code.
ADD . /app
# Copy the application's requirements.txt and run pip to install all
# dependencies into the virtualenv.
ADD requirements.txt /requirements.txt

# Create a virtualenv for dependencies. This isolates these packages from
# system-level packages.
RUN virtualenv -p python3 env && \
    . env/bin/activate && \
     pip install Flask && \
     pip install gunicorn && \
     pip install -t env/bin -r requirements.txt

CMD bash -x ${DOCKER_SCRIPTS_DIR}/startup.sh | tee -a ${DOCKER_LOGDIR}/startup.log