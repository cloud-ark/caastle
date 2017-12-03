import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError as IntegrityError

from server.common import fm_logger
from server.dbmodule import db_base

fmlogger = fm_logger.Logging()


class Environment(db_base.Base):
    __tablename__ = 'environment'
    __table_args__ = {'extend_existing': True}

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    name = sa.Column(sa.Text, nullable=False, unique=True)
    status = sa.Column(sa.String(32))
    env_definition = sa.Column(sa.Text, nullable=False)
    output_config = sa.Column(sa.Text)
    location = sa.Column(sa.Text)

    def __init__(self):
        pass

    @classmethod
    def to_json(self, env):
        env_json = {}
        env_json['name'] = env.name
        env_json['status'] = env.status
        env_json['env_definition'] = str(env.env_definition)
        env_json['output_config'] = str(env.output_config)
        env_json['location'] = env.location
        return env_json

    def get_by_name(self, env_name):
        env = ''
        try:
            session = db_base.get_session()
            env = session.query(Environment).filter_by(name=env_name).first()
            session.close()
        except IntegrityError as e:
            fmlogger.debug(e)
        return env

    def get(self, env_id):
        env = ''
        try:
            session = db_base.get_session()
            env = session.query(Environment).filter_by(id=env_id).first()
            session.close()
        except IntegrityError as e:
            fmlogger.debug(e)
        return env

    def get_all(self):
        env_list = ''
        try:
            session = db_base.get_session()
            env_list = session.query(Environment).all()
            session.close()
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
            session = db_base.get_session()
            session.add(self)
            session.commit()
            session.close()
        except IntegrityError as e:
            fmlogger.debug(e)
        return self.id

    def update(self, env_id, env_data):
        try:
            session = db_base.get_session()
            env = session.query(Environment).filter_by(id=env_id).first()
            if 'location' in env_data: env.location = env_data['location']
            if 'status' in env_data: env.status = env_data['status']
            if 'output_config' in env_data: env.output_config = env_data['output_config']
            if 'env_definition' in env_data: env.env_definition = env_data['env_definition']
            session.commit()
            session.close()
        except IntegrityError as e:
            fmlogger.debug(e)

    def delete(self, env_id):
        try:
            session = db_base.get_session()
            env = session.query(Environment).filter_by(id=env_id).first()
            session.delete(env)
            session.commit()
            session.close()
        except IntegrityError as e:
            fmlogger.debug(e)
