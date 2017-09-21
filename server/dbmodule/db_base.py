import os
from os.path import expanduser

import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlite3 import dbapi2 as sqlite

home_dir = expanduser("~")
APP_STORE_PATH = ("{home_dir}/.cld/data/deployments").format(home_dir=home_dir)
if not os.path.exists(APP_STORE_PATH):
    os.makedirs(APP_STORE_PATH)

DBFILE_NAME = "cld.sqlite"
DBFILE = APP_STORE_PATH + "/" + DBFILE_NAME

Base = declarative_base()
Session = sessionmaker()


def init():
    from objects import app
    from objects import environment
    DBFILE = APP_STORE_PATH + "/" + DBFILE_NAME
    engine = create_engine('sqlite+pysqlite:///' + DBFILE, module=sqlite, echo=True)
    Session.configure(bind=engine)
    metadata = MetaData(bind=engine)
    Base.metadata.create_all(bind=engine)


def delete_db_file(file_name):
    if os.path.exists(APP_STORE_PATH + "/" + file_name):
        os.remove(APP_STORE_PATH + "/" + file_name)