import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError as IntegrityError
from server.dbmodule import db_base

from server.common import fm_logger

fmlogger = fm_logger.Logging()

class App(db_base.Base):
    __tablename__ = 'app'

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String, nullable=False, unique=True)
    location = sa.Column(sa.String)
    version = sa.Column(sa.String)
    dep_target = sa.Column(sa.String)
    status = sa.Column(sa.String)
    output_config = sa.Column(sa.Text)
    env_id = sa.Column(sa.Integer)

    def __init__(self):
        #db_base.init()
        pass

    def get(self, app_id):
        app = ''
        try:
            session = db_base.Session()
            app = session.query(App).filter_by(id=app_id).first()
        except IntegrityError as e:
            fmlogger.debug(e)
        return app

    def insert(self, app_data):
        app = App()
        app.name = app_data['name']
        app.location = app_data['location']
        app.version = app_data['version']
        app.dep_target = app_data['dep_target']
        app.status = ''
        app.output_config = ''
        app.env_id = int(app_data['env_id'])
        try:
            session = db_base.Session()
            session.add(app)
            session.commit()
        except IntegrityError as e:
            fmlogger.debug(e)
        return app

    def update(self, app_id, app_data):
        try:
            session = db_base.Session()
            app = session.query(App).filter_by(id=app_id).first()
            if 'location' in app_data: app.location = app_data['location']
            if 'version' in app_data: app.version = app_data['version']
            if 'dep_target' in app_data: app.dep_target = app_data['dep_target']
            if 'status' in app_data: app.status = app_data['status']
            if 'output_config' in app_data: app.output_config = app_data['output_config']
            if 'env_id' in app_data: app.env_id = app_data['env_id']
            session.commit()
        except IntegrityError as e:
            fmlogger.debug(e)

    def delete(self, app_id):
        try:
            session = db_base.Session()
            app = session.query(App).filter_by(id=app_id).first()
            session.delete(app)
            session.commit()
        except IntegrityError as e:
            fmlogger.debug(e)