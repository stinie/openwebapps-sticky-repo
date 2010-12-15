import os
import site
import sys
import commands

here = os.path.dirname(os.path.abspath(__file__))
base = os.path.dirname(here)
secret_path = os.path.join(os.path.dirname(base), 'sync-server-private', 'sync')
site.addsitedir(os.path.join(here, 'lib-python'))
sys.path.insert(0, os.path.join(here, 'velruse'))
sys.path.insert(0, base)

from stickyrepo.wsgiapp import make_app as sticky_make_app

filename = os.path.join(secret_path, 'connections.py')
ns = {'__file__': filename}
execfile(filename, ns)
vars = ns['env_vars']
hostname = commands.getoutput('hostname').strip()
for name, value in vars[hostname].items():
    os.environ[name] = value

if not os.environ.get('CONFIG_MYSQL_SQLALCHEMY'):
    raise Exception('You must set $CONFIG_MYSQL_SQLALCHEMY')
if not os.environ.get('SILVER_APP_CONFIG'):
    raise Exception('You must set $SILVER_APP_CONFIG')
os.environ.setdefault('TEMP', '/tmp')

if 'setup' in sys.argv[1:]:
    data_app = sticky_make_app()
    data_app.create_database(None)
    print 'Database created'
    sys.exit()

sticky_app = sticky_make_app()

def application(environ, start_response):
    if environ.get('HTTPS') or os.environ.get('HTTPS'):
        environ['wsgi.url_scheme'] = 'https'
    environ['PATH_INFO'] = environ['SCRIPT_NAME'] + environ['PATH_INFO']
    environ['SCRIPT_NAME'] = ''
    return sticky_app(environ, start_response)
