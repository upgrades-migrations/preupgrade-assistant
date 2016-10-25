import logging

class ExceptionMiddleware(object):
    def process_exception(self, request, exception):
        logging.exception('Unhandled exception at {0}'.format(request.path))

