#!/bin/bash

. env/bin/activate
python --version
cd app
gunicorn -b :$PORT wsgi
