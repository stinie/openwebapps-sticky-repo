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
import time
import string
import hashlib
import hmac
import random


class Request(webob.Request):

    @property
    def session(self):
        return self.environ['beaker.session']

    _force_user_info = None

    @property
    def user_info(self):
        if self._force_user_info:
            return self._force_user_info
        value = self.cookies.get('user_info')
        if not value:
            return None
        value = check_value(value)
        if not value:
            return None
        value = json.loads(value)
        return value

    @user_info.setter
    def user_info(self, value):
        self._force_user_info = value

    @property
    def userid(self):
        return self.user_info and self.user_info.get('identifier')


def set_user_info(resp, value):
    value = json.dumps(value)
    cookie = sign_value(value)
    resp.set_cookie('user_info', cookie)


def create_salt(length=12):
    chars = string.ascii_letters + string.digits
    ## FIXME: os.urandom?
    return ''.join(
        random.choice(chars) for i in range(length))


def sign_value(value, secret=get_secret()):
    salt = create_salt()
    hash = hash_signature(salt, value, secret)
    data = urllib.quote(value, '')
    return data + '|' + salt + '|' + hash


def check_value(encoded, secret=get_secret()):
    data, salt, hash = encoded.split('|')
    value = str(urllib.unquote(data))
    check_hash = hash_signature(salt, value, secret)
    if hash != check_hash:
        ## FIXME: log
        return None
    return value


def hash_signature(salt, value, secret):
    hash = hmac.new(str(salt), str(value), hashlib.sha256)
    hash = hash.digest().encode('base64').replace('\n', '')
    return hash


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
        tmp = os.environ['TEMP']
        self.auth_session_app = SessionMiddleware(
            self.auth_app,
            data_dir=os.path.join(tmp, 'beaker'),
            lock_dir=os.path.join(tmp, 'beaker.lock'),
            type='cookie',
            cookie_expires=False,
            encrypt_key=get_secret(),
            validate_key=get_secret(),
            )
        self.debug = not is_production()
        self.store = SQLStore.from_silver()

    @wsgify(RequestClass=Request)
    def __call__(self, req):
        req.server_timestamp = time.time()
        if self.debug and 'X-Testing-User' in req.headers:
            # Not no save; we don't remember this in a cookie:
            req.user_info = {'identifier': req.headers['X-Testing-User'],
                             'displayName': req.headers['X-Testing-User']}
        if self.debug and req.path_info == '/.reset-time':
            return self.set_time(req)
        if req.path_info_peek() == 'auth':
            req.path_info_pop()
            return self.auth_session_app
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
        resp = self.data_app(req)
        resp.headers['X-Server-Timestamp'] = '%.3f' % req.server_timestamp
        return resp

    def set_time(self, req):
        import itertools
        new_time = itertools.count(1).next
        time.time = new_time
        return exc.HTTPNoContent()

    _data_app_re = re.compile(r'/data/\{(.*?)\}')

    def data_app(self, req):
        match = self._data_app_re.match(req.path_info)
        if not match:
            return exc.HTTPNotFound()
        username = urllib.unquote(match.group(1))
        rest = req.path_info[match.end():]
        rest = rest.strip('/')
        if username != req.userid:
            return exc.HTTPForbidden()
        if req.method == 'DELETE':
            if not rest:
                return self.delete_user(req, username)
            else:
                return self.delete_user_data(req, username, rest)
        elif rest.endswith('/last_updated'):
            type = rest[:-len('/last_updated')]
            return self.user_last_updated(req, username, type)
        elif req.method == 'GET':
            return self.user_data(req, username, rest)
        elif req.method == 'POST':
            return self.update_user_data(req, username, rest)
        else:
            ## FIXME: not sure this is a good default:
            return exc.HTTPForbidden()

    def delete_user(self, req, username):
        self.store.delete_user(username)
        return exc.HTTPNoContent()

    def delete_user_data(self, req, username, type):
        self.store.delete_user_data(username, type)
        return exc.HTTPNoContent()

    def user_last_updated(self, req, username, type):
        d = {'date': self.store.user_last_updated(username, type)}
        return self.json_response(d)

    def user_data(self, req, username, type):
        last_time = self.store.user_last_updated(username, type)
        if last_time:
            last_time = time.mktime(last_time.timetuple())
        n = float(req.headers.get('X-If-Modified-Since-Timestamp', 0))
        if last_time and n and n <= last_time:
            return exc.HTTPNotModified()
        return self.json_response(self.store.user_data(username, type))

    def update_user_data(self, req, username, type):
        body = json.loads(req.body)
        self.store.update_user_data(username, type, body)
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
        #req.session['user_token'] = token
        dest = urlparse.urljoin(req.url, '/auth/auth_info')
        api_params = dict(
            token=token,
            format='json',
            )
        http_response = urllib2.urlopen(dest, urllib.urlencode(api_params))
        auth_info = json.loads(http_response.read())
        #req.session.delete()
        resp = exc.HTTPFound(location='/')
        set_user_info(resp, auth_info['profile'])
        resp.delete_cookie('beaker.session.id')
        return resp

    def logout(self, req):
        #req.session.delete()
        came_from = urlparse.urljoin(
            req.application_url, req.params.get('came_from', '/'))
        resp = exc.HTTPFound(location=came_from)
        resp.delete_cookie('user_info')
        return resp

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
    #tmp = os.environ['TEMP']
    #app = SessionMiddleware(
    #    app,
    #    data_dir=os.path.join(tmp, 'beaker'),
    #    lock_dir=os.path.join(tmp, 'beaker.lock'),
    #    type='cookie',
    #    cookie_expires=False,
    #    encrypt_key=get_secret(),
    #    validate_key=get_secret(),
    #    # Signs, but does not encrypt the cookie:
    #    #secret=get_secret(),
    #    )
    return app
