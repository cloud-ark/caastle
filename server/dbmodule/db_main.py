import os

import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy import MetaData
from sqlite3 import dbapi2 as sqlite

from dbmodule import db_base
from objects import app
from objects import environment
from objects import resource
from server.common import fm_logger

fmlogger = fm_logger.Logging()

DBFILE = db_base.APP_STORE_PATH + "/" + db_base.DBFILE_NAME
engine = create_engine('sqlite+pysqlite:///' + DBFILE, module=sqlite, echo=True)
db_base.Session.configure(bind=engine)
metadata = MetaData(bind=engine)

try:
    app.App.__table__.create(bind=engine)
    environment.Environment.__table__.create(bind=engine)
    resource.Resource.__table__.create(bind=engine)
except Exception as e:
    fmlogger.debug(e)

def delete_db_file(file_name):
    if os.path.exists(APP_STORE_PATH + "/" + file_name):
        os.remove(APP_STORE_PATH + "/" + file_name)
