FROM gcr.io/ordinal-ember-163410/python-appengine-sumo-base
VOLUME /tmp

ENV SUMOLOGIC_BASEDIR /opt/SumoCollector
ENV SUMOLOGIC_CONFDIR ${SUMOLOGIC_BASEDIR}/config
COPY ./sumologic_sources.json ${SUMOLOGIC_CONFDIR}/sumologic_sources.json

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# INSTALL gcp credentials
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
CMD export app_folder = reporting
RUN mkdir -p /opt/behalf/cto/reporting/log
RUN mkdir -p /opt/behalf/cto/reporting/data

ENV DOCKER_BASEDIR /opt/docker
ENV DOCKER_LOGDIR  ${DOCKER_BASEDIR}/log
ENV DOCKER_SCRIPTS_DIR  ${DOCKER_BASEDIR}/scripts


RUN virtualenv --no-download /env -p python3.6
# Set virtualenv environment variables. This is equivalent to running
# source /env/bin/activate
ENV VIRTUAL_ENV /env
ENV PATH /env/bin:$PATH
COPY requirements.txt /app/
RUN pip install -r requirements.txt
RUN mkdir app
COPY ./app ./app/

CMD bash -x ${DOCKER_SCRIPTS_DIR}/startup.sh reporting | tee -a ${DOCKER_LOGDIR}/startup.log

