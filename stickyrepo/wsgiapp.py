import os
import re
from webob.dec import wsgify
from webob import exc
import webob
from velruse.app import VelruseApp
from beaker.middleware import SessionMiddleware
from silversupport.secret import get_secret
from silversupport.env import is_production
import urlparse
import urllib
import urllib2
try:
    import simplejson as json
except ImportError:
    import json
from stickyrepo.sqlstore import SQLStore


class Request(webob.Request):

    @property
    def session(self):
        return self.environ['beaker.session']

    @property
    def user_info(self):
        return self.session.get('auth')

    @user_info.setter
    def user_info(self, value):
        self.session['auth'] = value
        self.session.save()

    @property
    def userid(self):
        return self.user_info and self.user_info.get('identifier')


class Application(object):

    def __init__(self):
        config_dir = os.environ['SILVER_APP_CONFIG']
        config = None
        for name in ['local.yaml', 'velruse.yaml']:
            if os.path.exists(os.path.join(config_dir, name)):
                config = os.path.join(config_dir, name)
                break
        tmp = os.environ['TEMP']
        self.auth_app = VelruseApp(
            config,
            {'Store': {
                'Type': 'SQL',
                'DB': os.environ['CONFIG_MYSQL_SQLALCHEMY'],
                },
             'OpenID Store': {
                 'Type': 'openid.store.filestore:FileOpenIDStore',
                 'directory': os.path.join(tmp, 'openid'),
                 }
             })
        self.debug = not is_production()
        self.store = SQLStore.from_silver()

    @wsgify(RequestClass=Request)
    def __call__(self, req):
        if self.debug and 'X-Testing-User' in req.headers:
            # Not no save; we don't remember this in a cookie:
            req.user_info = {'identifier': req.headers['X-Testing-User'],
                             'displayName': req.headers['X-Testing-User']}
        if req.path_info_peek() == 'auth':
            req.path_info_pop()
            return self.auth_app
        if req.path_info == '/.create-database':
            ## FIXME: and internal check
            return self.create_database(req)
        if req.path_info == '/success':
            return self.success(req)
        if req.path_info == '/logout' or req.path_info == '/logout/':
            return self.logout(req)
        if req.path_info.rstrip('/') == '/login-status':
            return self.login_status(req)
        if not req.userid:
            raise exc.HTTPTemporaryRedirect(
                location='/login/')
        return self.data_app(req)

    _data_app_re = re.compile(r'/data/(\{.*?\})')

    def data_app(self, req):
        match = self._data_app_re.match(req.path_info)
        if not match:
            return exc.HTTPNotFound()
        username = match.group(1)
        rest = req.path_info[match.end():]
        if req.method == 'DELETE':
            if not rest:
                return self.delete_user(req, username)
            else:
                return exc.HTTPMethodNotAllowed()
        elif rest == '/last_updated':
            return self.user_last_updated(req, username)
        elif req.method == 'GET':
            return self.user_data(req, username)
        elif req.method == 'POST':
            return self.update_user_data(req, username)
        else:
            ## FIXME: not sure this is a good default:
            return exc.HTTPForbidden()

    def delete_user(self, req, username):
        self.store.delete_user(username)
        return exc.HTTPNoContent()

    def user_last_updated(self, req, username):
        d = {'date': self.store.user_last_updated(username)}
        return self.json_response(d)

    def user_data(self, req, username):
        return self.json_response(self.store.user_data(username))

    def update_user_data(self, req, username):
        body = json.loads(req.body)
        self.store.update_user_data(username, body)
        return exc.HTTPNoContent()

    def debug_app(self, req):
        s = ['<pre>']
        for key, value in sorted(req.environ.items()):
            s.append('%s=%r\n' % (key, value))
        s.append('Session: %r\n' % req.session)
        s.append('</pre>')
        return ''.join(s)

    def create_database(self, req):
        self.auth_app.store.create()
        self.store.create()
        return ''

    def success(self, req):
        token = req.POST['token']
        req.session['user_token'] = token
        dest = urlparse.urljoin(req.url, '/auth/auth_info')
        api_params = dict(
            token=token,
            format='json',
            )
        http_response = urllib2.urlopen(dest, urllib.urlencode(api_params))
        auth_info = json.loads(http_response.read())
        req.user_info = auth_info['profile']
        return exc.HTTPFound(location='/')

    def logout(self, req):
        req.session.delete()
        came_from = urlparse.urljoin(
            req.application_url, req.params.get('came_from', '/'))
        return exc.HTTPFound(location=came_from)

    def login_status(self, req):
        return self.json_response(req.user_info)

    def json_response(self, data, **kw):
        if not isinstance(data, basestring):
            data = json.dumps(data)
        return webob.Response(
            data,
            content_type='application/json',
            **kw)

def make_app():
    app = Application()
    tmp = os.environ['TEMP']
    app = SessionMiddleware(
        app,
        data_dir=os.path.join(tmp, 'beaker'),
        lock_dir=os.path.join(tmp, 'beaker.lock'),
        type='cookie',
        cookie_expires=False,
        encrypt_key=get_secret(),
        validate_key=get_secret(),
        # Signs, but does not encrypt the cookie:
        #secret=get_secret(),
        )
    return app
