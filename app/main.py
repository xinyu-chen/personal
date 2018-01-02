import logging

from flask import Flask

from app.paymentReport.peeriq_upload import uploadXml

application = Flask(__name__)

# def secure(func):
#     '''
#     makes the given function be only accessible from cron jobs
#     '''
#     async def secured(request, *args, **kwargs):
#         if not 'x-appengine-cron' in request.headers:
#             return response.text(body='FORBIDDEN', status=403)
#         return await func(request, *args, **kwargs)
#
#     return secured

@application.route('/')
def hello():
    logging.info('hello')
    return 'Hello World!'

@application.route('/keep-alive')
def keepalive():
    return '200 OK'

@application.errorhandler(500)
def server_error(e):
    logging.exception('An error occurred during a request.')
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(e), 500


@application.route('/payment/uploadXml')
def paymentUploadXml():
    uploadXml()
    return 'run'

if __name__ == '__main__':
    # This is used when running locally. Gunicorn is used to run the
    # application on Google App Engine. See entrypoint in app.yaml.
    logging.basicConfig(filename='/opt/behalf/cto/reporting/log/reporting.log', level=logging.INFO)
    application.run(port=8080, debug=True)