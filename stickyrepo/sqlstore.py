import os
from stickyrepo.abstractstore import AbstractStore
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base, Column
from sqlalchemy.sql import select, delete
from sqlalchemy import String, Text, DateTime
from sqlalchemy.sql import func
try:
    import simplejson as json
except ImportError:
    import json

SQLBase = declarative_base()


class UserStorage(SQLBase):
    __tablename__ = 'sync_storage'
    userid = Column(String(255), primary_key=True, nullable=False)
    data = Column(Text(), nullable=False)
    last_updated = Column(DateTime())


class SQLStore(AbstractStore):

    def __init__(self, engine):
        self.engine = engine
        UserStorage.metadata.bind = engine

    def delete_user(self, username):
        self.engine.execute(
            delete(UserStorage.__table__,
                   UserStorage.__table__.c.userid == username))

    def user_last_updated(self, username):
        res = self.engine.execute(
            select([UserStorage.__table__.c.last_updated],
                   UserStorage.__table__.c.userid == username))
        res = res.fetchone()
        if res is None:
            return None
        return res[0]

    def user_data(self, username):
        res = self.engine.execute(
            select([UserStorage.__table__.c.data,
                    UserStorage.__table__.c.last_updated],
                   UserStorage.__table__.c.userid == username))
        res = res.fetchone()
        if res is None:
            return None
        ## FIXME: integrate last_updated somehow?
        return json.loads(res[0])

    def update_user_data(self, username, new_data):
        new_data = json.dumps(new_data)
        res = self.engine.execute(
            UserStorage.__table__.update(UserStorage.__table__.c.userid == username),
            data=new_data,
            last_updated=func.now())
        if not res.rowcount:
            self.engine.execute(
                UserStorage.__table__.insert(),
                userid=username,
                data=new_data,
                last_updated=func.now())

    @classmethod
    def from_silver(cls):
        sqluri = os.environ['CONFIG_MYSQL_SQLALCHEMY']
        engine = create_engine(sqluri,
                               pool_size=100,
                               pool_recycle=3600,
                               logging_name='stickyrepo')
        return cls(engine)

    def create(self):
        UserStorage.__table__.create(checkfirst=True)
