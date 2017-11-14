import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError as IntegrityError

from server.common import fm_logger
from server.dbmodule import db_base

fmlogger = fm_logger.Logging()


class Container(db_base.Base):
    __tablename__ = 'container'
    __table_args__ = {'extend_existing': True}

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String, nullable=False, unique=True)
    dep_target = sa.Column(sa.String)
    status = sa.Column(sa.String)
    output_config = sa.Column(sa.Text)
    cont_store_path = sa.Column(sa.Text)

    def __init__(self):
        pass

    @classmethod
    def to_json(self, cont):
        cont_json = {}
        cont_json['id'] = cont.id
        cont_json['name'] = cont.name
        cont_json['dep_target'] = cont.dep_target
        cont_json['status'] = cont.status
        cont_json['output_config'] = str(cont.output_config)
        cont_json['cont_store_path'] = str(cont.cont_store_path)
        return cont_json

    def get(self, name):
        cont = ''
        try:
            session = db_base.get_session()
            cont = session.query(Container).filter_by(name=name).first()
            session.close()
        except IntegrityError as e:
            fmlogger.debug(e)
        return cont

    def get_all(self):
        cont_list = ''
        try:
            session = db_base.get_session()
            cont_list = session.query(Container).all()
            session.close()
        except IntegrityError as e:
            fmlogger.debug(e)
        return cont_list

    def insert(self, cont_data):
        self.name = cont_data['cont_name']
        self.dep_target = cont_data['dep_target']
        self.status = 'building'
        self.output_config = ''
        self.cont_store_path = cont_data['cont_store_path']
        try:
            session = db_base.get_session()
            session.add(self)
            session.commit()
            session.close()
        except IntegrityError as e:
            fmlogger.debug(e)
        return self.id

    def update(self, cont_name, cont_data):
        try:
            session = db_base.get_session()
            cont = session.query(Container).filter_by(name=cont_name).first()
            if 'dep_target' in cont_data: cont.dep_target = cont_data['dep_target']
            if 'status' in cont_data: cont.status = cont_data['status']
            if 'output_config' in cont_data: cont.output_config = cont_data['output_config']
            session.commit()
            session.close()
        except IntegrityError as e:
            fmlogger.debug(e)

    def delete(self, cont_name):
        try:
            session = db_base.get_session()
            cont = session.query(Container).filter_by(name=cont_name).first()
            session.delete(cont)
            session.commit()
            session.close()
        except IntegrityError as e:
            fmlogger.debug(e)
