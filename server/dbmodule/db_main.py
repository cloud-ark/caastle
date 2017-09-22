import os

import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy import MetaData

from sqlite3 import dbapi2 as sqlite

from dbmodule import db_base

from objects import app
from objects import environment

DBFILE = db_base.APP_STORE_PATH + "/" + db_base.DBFILE_NAME
engine = create_engine('sqlite+pysqlite:///' + DBFILE, module=sqlite, echo=True)
db_base.Session.configure(bind=engine)
metadata = MetaData(bind=engine)
db_base.Base.metadata.create_all(bind=engine)

def delete_db_file(file_name):
    if os.path.exists(APP_STORE_PATH + "/" + file_name):
        os.remove(APP_STORE_PATH + "/" + file_name)
