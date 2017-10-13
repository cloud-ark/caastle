import os
from os.path import expanduser

from sqlalchemy import create_engine
from sqlite3 import dbapi2 as sqlite

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

home_dir = expanduser("~")
APP_STORE_PATH = ("{home_dir}/.cld/data/deployments").format(home_dir=home_dir)
if not os.path.exists(APP_STORE_PATH):
    os.makedirs(APP_STORE_PATH)

DBFILE_NAME = "cld.sqlite"
DBFILE = APP_STORE_PATH + "/" + DBFILE_NAME

engine = create_engine('sqlite+pysqlite:///' + DBFILE, module=sqlite, echo=True)

Session = sessionmaker(expire_on_commit=False)


def get_session():
    return Session(bind=engine)
