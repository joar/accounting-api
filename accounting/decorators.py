# Part of accounting-api project:
# https://gitorious.org/conservancy/accounting-api
# License: AGPLv3-or-later

from functools import wraps

from flask import jsonify, request

from accounting.exceptions import AccountingException


def jsonify_exceptions(func):
    '''
    Wraps a Flask endpoint and catches any AccountingException-based
    exceptions which are returned to the client as JSON.
    '''
    @wraps(func)
    def wrapper(*args, **kw):
        try:
            return func(*args, **kw)
        except AccountingException as exc:
            return jsonify(error=exc)

    return wrapper


def cors(origin_callback=None):
    '''
    Flask endpoint decorator.

    Example:

    .. code-block:: python

        @app.route('/cors-endpoint', methods=['GET', 'OPTIONS'])
        @cors()
        def cors_endpoint():
            return jsonify(message='This is accessible via a cross-origin XHR')

        # Or if you want to control the domains this resource can be requested
        # from via CORS:
        domains = ['http://wandborg.se', 'http://sfconservancy.org']

        def restrict_domains(origin):
            return ' '.join(domains)

        @app.route('/restricted-cors-endpoint')
        @cors(restrict_domains)
        def restricted_cors_endpoint():
            return jsonify(
                message='This is accessible from %s' % ', '.join(domains))

    :param function origin_callback: A callback that takes one str() argument
        containing the ``Origin`` HTTP header from the :data:`request` object.
        This can be used to filter out which domains the resource can be
        requested via CORS from.
    '''
    if origin_callback is None:
        origin_callback = allow_all_origins

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kw):
            response = func(*args, **kw)
            cors_headers = {
                'Access-Control-Allow-Origin':
                    origin_callback(request.headers.get('Origin')) or '*',
                'Access-Control-Allow-Credentials': 'true',
                'Access-Control-Max-Age': 3600,
                'Access-Control-Allow-Methods': 'POST, GET, DELETE',
                'Access-Control-Allow-Headers':
                    'Accept, Content-Type, Connection, Cookie'
            }

            for key, val in cors_headers.items():
                response.headers[key] = val

            return response

        return wrapper

    return decorator


def allow_all_origins(origin):
    return origin
