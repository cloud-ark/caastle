import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError as IntegrityError
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
        db_base.init()

    def get(self, res_id):
        env = ''
        try:
            session = db_base.Session()
            res = session.query(Resource).filter_by(id=res_id).first()
        except IntegrityError as e:
            fmlogger.debug(e)
        return res

    def insert(self, res_data):
        res = Resource()
        res.env_id = res_data['env_id']
        res.output_config = res_data['output_config']
        res.type = res_data['type']
        res.input_config = res_data['input_config']
        res.status = ''
        try:
            session = db_base.Session()
            session.add(res)
            session.commit()
        except IntegrityError as e:
            fmlogger.debug(e)
        return res

