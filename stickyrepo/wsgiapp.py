import os
import yaml
from webob.dec import wsgify
from velruse.app import VelruseApp
from beaker.middleware import SessionMiddleware


class Application(object):

    def __init__(self):
        config_dir = os.environ['SILVER_APP_CONFIG']
        config = None
        for name in ['local.yaml', 'velruse.yaml']:
            if os.path.exists(os.path.join(config_dir, name)):
                config = os.path.join(config_dir, name)
                break
        tmp = os.environ['TEMP']
        self.velruse_app = VelruseApp(
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
        with open(config) as fp:
            config_data = yaml.load(fp.read())

        self.auth_app = SessionMiddleware(
            self.velruse_app,
            data_dir=os.path.join(tmp, 'beaker'),
            lock_dir=os.path.join(tmp, 'beaker.lock'),
            type='cookie',
            cookie_expires=False,
            encrypt_key=config_data['Beaker']['encrypt_key'],
            validate_key=config_data['Beaker']['validate_key'],
            # Signs, but does not encrypt the cookie:
            #secret=get_secret(),
            )

    @wsgify
    def __call__(self, req):
        if req.path_info_peek() == 'auth':
            req.path_info_pop()
            return self.auth_app
        if req.path_info == '/.create-database':
            ## FIXME: and internal check
            return self.create_database(req)
        return '''
<form action="/auth/facebook/auth" method="post">
<input type="hidden" name="end_point" value="http://localhost:8080/success" />
<input type="hidden" name="scope" value="publish_stream,create_event" />
<input type="submit" value="Login with Facebook" />
</form>

<form action="/auth/yahoo/auth" method="post">
<input type="hidden" name="end_point" value="http://localhost:8080/success" />
<input type="hidden" name="oauth" value="true" />
<input type="submit" value="Login with Yahoo" />
</form>

<form action="/auth/twitter/auth" method="post">
<input type="hidden" name="end_point" value="http://localhost:8080/success" />
<input type="submit" value="Login with Twitter" />
</form>

<form action="/auth/openid/auth" method="post">
<input type="hidden" name="end_point" value="http://localhost:8080/success" />
ID: <input type="text" name="openid_identifier" />
<input type="submit" value="Login with OpenID" />
</form>

'''

    def create_database(self, req):
        self.velruse_app.store.create()
        return ''
