import os
from os.path import expanduser

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

Session = sessionmaker()

engine = ''

home_dir = expanduser("~")
APP_STORE_PATH = ("{home_dir}/.cld/data/deployments").format(home_dir=home_dir)
if not os.path.exists(APP_STORE_PATH):
    os.makedirs(APP_STORE_PATH)

DBFILE_NAME = "cld.sqlite"
DBFILE = APP_STORE_PATH + "/" + DBFILE_NAME