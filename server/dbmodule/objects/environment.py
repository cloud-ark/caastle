import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError as IntegrityError
from sqlalchemy import create_engine
from sqlite3 import dbapi2 as sqlite

from server.common import fm_logger
from server.dbmodule import db_base

fmlogger = fm_logger.Logging()

class Environment(db_base.Base):
    __tablename__ = 'environment'

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    name = sa.Column(sa.Text, nullable=False)
    status = sa.Column(sa.String(32))
    env_definition = sa.Column(sa.Text, nullable=False)
    output_config = sa.Column(sa.Text)
    location = sa.Column(sa.Text)

    def __init__(self):
        DBFILE = db_base.APP_STORE_PATH + "/" + db_base.DBFILE_NAME
        engine = create_engine('sqlite+pysqlite:///' + DBFILE, module=sqlite, echo=True)
        db_base.Session.configure(bind=engine)

    @classmethod
    def to_json(self, env):
        env_json = {}
        env_json['id'] = env.id
        env_json['name'] = env.name
        env_json['status'] = env.status
        env_json['env_definition'] = str(env.env_definition)
        env_json['output_config'] = str(env.output_config)
        env_json['location'] = env.location
        return env_json

    def get(self, env_id):
        env = ''
        try:
            session = db_base.Session()
            env = session.query(Environment).filter_by(id=env_id).first()
        except IntegrityError as e:
            fmlogger.debug(e)
        return env

    def get_all(self):
        env_list = ''
        try:
            session = db_base.Session()
            env_list = session.query(Environment).all()
        except IntegrityError as e:
            fmlogger.debug(e)
        return env_list

    def insert(self, env_data):
        self.name = env_data['name']
        self.location = env_data['location']
        self.env_definition = str(env_data['env_definition'])
        self.status = 'creating'
        output_config = {}
        output_config['env_version_stamp'] = env_data['env_version_stamp']
        self.output_config = str(output_config)
        try:
            session = db_base.Session()
            session.add(self)
            session.commit()
        except IntegrityError as e:
            fmlogger.debug(e)
        return self.id

    def update(self, env_id, env_data):
        try:
            session = db_base.Session()
            env = session.query(Environment).filter_by(id=env_id).first()
            if 'location' in env_data: env.location = env_data['location']
            if 'status' in env_data: env.status = env_data['status']
            if 'output_config' in env_data: env.output_config = env_data['output_config']
            if 'env_definition' in env_data: env.env_definition = env_data['env_definition']
            session.commit()
        except IntegrityError as e:
            fmlogger.debug(e)

    def delete(self, env_id):
        try:
            session = db_base.Session()
            env = session.query(Environment).filter_by(id=env_id).first()
            session.delete(env)
            session.commit()
        except IntegrityError as e:
            fmlogger.debug(e)