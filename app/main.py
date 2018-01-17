import logging
from functools import wraps
from flask import Flask, jsonify, request, Response
from BQService import BQService

def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == 'behalf' and password == 'zazma123'

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

# Creates a wrapper authentication function around a function. Credentials will be needed to run the function within
def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


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


@application.route('/account/<id>')
@requires_auth
def export_json(id):
    ''' Extracts data from BQ and return results in JSON format'''
    data = BQService.get_data(id)
    return jsonify(data)


if __name__ == '__main__':
    # This is used when running locally. Gunicorn is used to run the
    # application on Google App Engine. See entrypoint in app.yaml.
    #logging.basicConfig(filename='/opt/behalf/cto/reporting/log/reporting.log', level=logging.INFO)
    application.run(port=8080, debug=True)
