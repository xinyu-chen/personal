#!/bin/bash

. env/bin/activate
python --version
cd app
export app_folder=$1
echo app_folder = $app_folder
gunicorn --access-logfile /opt/behalf/cto/$app_folder/log/${app_folder}_access.log --error-logfile /opt/behalf/cto/$app_folder/log/${app_folder}_error.log --log-file /opt/behalf/cto/$app_folder/log/$app_folder.log -b :$PORT wsgi
