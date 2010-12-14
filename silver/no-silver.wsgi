import os
import site
import sys

here = os.path.dirname(os.path.abspath(__file__))
base = os.path.dirname(here)
site.addsitedir(os.path.join(here, 'lib-python'))
sys.path.insert(0, os.path.join(here, 'velruse'))
sys.path.insert(0, base)

from stickyrepo.wsgiapp import make_app as sticky_make_app

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

application = sticky_make_app()
