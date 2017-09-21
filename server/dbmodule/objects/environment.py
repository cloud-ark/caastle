import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError as IntegrityError
from server.dbmodule import db_base

from server.common import fm_logger

fmlogger = fm_logger.Logging()

class Environment(db_base.Base):
    __tablename__ = 'environment'
    
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String, nullable=False)
    status = sa.Column(sa.String)
    env_definition = sa.Column(sa.Text)
    output_config = sa.Column(sa.Text)
    location = sa.Column(sa.String)
    
    def __init__(self):
        db_base.init()

    def get(self, env_id):
        env = ''
        try:
            session = db_base.Session()
            env = session.query(Environment).filter_by(id=env_id).first()
        except IntegrityError as e:
            fmlogger.debug(e)
        return env
    
    def insert(self, env_data):
        env = Environment()
        env.name = env_data['name']
        env.location = env_data['location']
        env.dep_target = env_data['dep_target']
        env.env_definition = env_data['env_definition']
        env.status = ''
        env.output_config = ''
        try:
            session = db_base.Session()
            session.add(env)
            session.commit()
        except IntegrityError as e:
            fmlogger.debug(e)
        return env

