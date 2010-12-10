#!/usr/bin/env python
import os
import site
import sys

here = os.path.dirname(os.path.abspath(__file__))
silver = os.path.join(here, 'silver')
site.addsitedir(os.path.join(silver, 'lib-python'))
sys.path.insert(0, os.path.join(silver, 'velruse'))
sys.path.insert(0, here)

from paste.httpserver import serve
from paste.urlparser import StaticURLParser
from paste.cascade import Cascade
from stickyrepo.wsgiapp import make_app as sticky_make_app


def make_app():
    data_app = sticky_make_app()
    site_dir = os.path.join(os.path.dirname(here), 'site')
    static_app = StaticURLParser(site_dir, cache_max_age=0)
    if not os.path.exists(site_dir):
        print "Error: %s doesn't exists" % site_dir
        sys.exit(1)
    app = Cascade([static_app, data_app])
    return app


def serve_app(port, database, config, setup):
    os.environ['CONFIG_MYSQL_SQLALCHEMY'] = database
    os.environ['DEBUG_STICKYREPO'] = '1'
    os.environ['SILVER_APP_CONFIG'] = config
    os.environ['TEMP'] = '/tmp'
    if setup:
        data_app = sticky_make_app()
        data_app.create_database(None)
        print 'Database created'
    else:
        app = make_app()
        serve(app, port=port)


def main():
    import optparse
    parser = optparse.OptionParser(
        usage='%prog --db=SOMETHING')
    parser.add_option(
        '-d', '--db',
        help="Database to connect to (SQLAlchemy connection string); you might want to try sqlite:///test.db")
    parser.add_option(
        '-p', '--port',
        default='8080',
        help='Port to serve on (default 8080)')
    parser.add_option(
        '--config',
        default=os.path.join(here, 'silver', 'default-config'),
        help='Location where the velruse.yaml or local.yaml config file is (for login API keys).  Clone git@github.com:mozilla/openwebapps-private.git to get our keys (in openwebapps-private/sync).')
    parser.add_option(
        '--setup',
        action='store_true',
        help="Setup the database (don't run the server)")
    options, args = parser.parse_args()
    port = int(options.port)
    if not options.db:
        parser.error('You must give --db')
    serve_app(port, options.db, options.config, options.setup)


if __name__ == '__main__':
    main()
