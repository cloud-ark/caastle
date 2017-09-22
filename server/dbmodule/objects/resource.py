import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError as IntegrityError
from sqlalchemy import create_engine
from sqlite3 import dbapi2 as sqlite

from server.dbmodule import db_base
from server.common import fm_logger

fmlogger = fm_logger.Logging()

class Resource(db_base.Base):
    __tablename__ = 'resource'
    
    id = sa.Column(sa.Integer, primary_key=True)
    env_id = sa.Column(sa.Integer)
    output_config = sa.Column(sa.Text)
    type = sa.Column(sa.String, nullable=False)
    status = sa.Column(sa.String)
    input_config = sa.Column(sa.Text)
    filtered_description = sa.Column(sa.Text)
    detailed_description = sa.Column(sa.Text)
    
    def __init__(self):
        DBFILE = db_base.APP_STORE_PATH + "/" + db_base.DBFILE_NAME
        engine = create_engine('sqlite+pysqlite:///' + DBFILE, module=sqlite, echo=True)
        db_base.Session.configure(bind=engine)

    def get(self, res_id):
        res = ''
        try:
            session = db_base.Session()
            res = session.query(Resource).filter_by(id=res_id).first()
        except IntegrityError as e:
            fmlogger.debug(e)
        return res

    def insert(self, res_data):
        self.env_id = res_data['env_id']
        self.output_config = res_data['output_config']
        self.type = res_data['type']
        self.input_config = res_data['input_config']
        self.status = 'creating'
        try:
            session = db_base.Session()
            session.add(res)
            session.commit()
        except IntegrityError as e:
            fmlogger.debug(e)
        return res

    def get_by_env(self, env_id):
        res_list = ''
        try:
            session = db_base.Session()
            res_list = session.query(Resource).filter_by(env_id=env_id).all()
        except IntegrityError as e:
            fmlogger.debug(e)
        return res_list