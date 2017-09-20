import os
from os.path import expanduser

import sqlalchemy

from sqlalchemy import create_engine
from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from sqlite3 import dbapi2 as sqlite

#from server.dbmodule.objects import app
import objects.app

home_dir = expanduser("~")
APP_STORE_PATH = ("{home_dir}/.cld/data/deployments").format(home_dir=home_dir)
if not os.path.exists(APP_STORE_PATH):
    os.makedirs(APP_STORE_PATH)

DBFILE = APP_STORE_PATH + "/cld.sqlite"

engine = create_engine('sqlite+pysqlite:///' + DBFILE, module=sqlite, echo=True)

Session = sessionmaker(bind=engine)

Base = declarative_base()

metadata = MetaData(bind=engine)

def init():
    Base.metadata.create_all(bind=engine)


