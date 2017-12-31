#!/bin/bash -v
set -x

HOSTNAME=`curl -s http://169.254.169.254/computeMetadata/v1beta1/instance/hostname`

SUMO_CONF_FILE="/etc/sumo.conf"
SUMO_CONF_BEHALF_TEMPLATE="/etc/sumo.conf.behalf"

if [ -f ${SUMO_CONF_BEHALF_TEMPLATE} ] ; then
	sed -i 's/ //g' ${SUMO_CONF_BEHALF_TEMPLATE}
	mv ${SUMO_CONF_BEHALF_TEMPLATE} ${SUMO_CONF_FILE}
fi

sed -i "s|@@INSTANCE_ID@@|${HOSTNAME}|g" /opt/SumoCollector/config/sumologic_sources.json

/etc/init.d/collector start

. env/bin/activate
python --version
cd app
gunicorn -b :$PORT wsgi
