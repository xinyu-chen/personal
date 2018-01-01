FROM gcr.io/google-appengine/python
LABEL python_version=python3.6
VOLUME /tmp

ENV DOCKER_BASEDIR /opt/docker
ENV DOCKER_LOGDIR  ${DOCKER_BASEDIR}/log
ENV DOCKER_SCRIPTS_DIR  ${DOCKER_BASEDIR}/scripts
ENV SUMOLOGIC_BASEDIR /opt/SumoCollector
ENV SUMOLOGIC_CONFDIR ${SUMOLOGIC_BASEDIR}/config

RUN apt-get update && apt-get install -y curl nano

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# add sumo files
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

ENV SUMO_LATEST_DEBPKG_NAME /tmp/sumocollector.deb
ENV SUMO_INSTALLER_URL https://collectors.sumologic.com/rest/download/deb/64

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# INSTALL SUMO LOGIC COLLECTOR
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
RUN wget -O ${SUMO_LATEST_DEBPKG_NAME} ${SUMO_INSTALLER_URL} && \
 if [ -f ${SUMO_LATEST_DEBPKG_NAME} ] ; then \
         dpkg -i ${SUMO_LATEST_DEBPKG_NAME} ; \
         chown -R root:root /opt/SumoCollector ; \
         rm ${SUMO_LATEST_DEBPKG_NAME} ; \
    fi

ADD sumo.conf /etc/sumo.conf.behalf
#ADD sumologic_sources.json ${SUMOLOGIC_CONFDIR}/sumologic_sources.json

RUN mkdir -p ${DOCKER_SCRIPTS_DIR}
ADD startup.sh ${DOCKER_SCRIPTS_DIR}/startup.sh
RUN chmod +x ${DOCKER_SCRIPTS_DIR}/startup.sh
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

RUN mkdir -p ${DOCKER_LOGDIR}

CMD tail -f /dev/null
