import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError as IntegrityError
from sqlalchemy import create_engine
from sqlite3 import dbapi2 as sqlite

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
        DBFILE = db_base.APP_STORE_PATH + "/" + db_base.DBFILE_NAME
        engine = create_engine('sqlite+pysqlite:///' + DBFILE, module=sqlite, echo=True)
        db_base.Session.configure(bind=engine)

    @classmethod
    def to_json(self, app):
        app_json = {}
        app_json['id'] = app.id
        app_json['name'] = app.name
        app_json['location'] = app.location
        app_json['version'] = app.version
        app_json['dep_target'] = app.dep_target
        app_json['status'] = app.status
        app_json['output_config'] = str(app.output_config)
        app_json['env_id'] = app.env_id
        return app_json

    def get(self, app_id):
        app = ''
        try:
            session = db_base.Session()
            app = session.query(App).filter_by(id=app_id).first()
        except IntegrityError as e:
            fmlogger.debug(e)
        return app

    def get_all(self):
        app_list = ''
        try:
            session = db_base.Session()
            app_list = session.query(App).all()
        except IntegrityError as e:
            fmlogger.debug(e)
        return app_list

    def insert(self, app_data):
        self.name = app_data['name']
        self.location = app_data['location']
        self.version = app_data['version']
        self.dep_target = app_data['dep_target']
        self.status = 'deploying'
        self.output_config = ''
        self.env_id = app_data['env_id']
        try:
            session = db_base.Session()
            session.add(self)
            session.commit()
        except IntegrityError as e:
            fmlogger.debug(e)
        return self.id

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