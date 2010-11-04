from webob.dec import wsgify


class Application(object):

    @wsgify
    def __call__(self, req):
        return 'hey'
