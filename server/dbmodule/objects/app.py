import sqlalchemy as sa
from server.dbmodule import db_base

class App(db_base.Base):
    __tablename__ = 'app1'

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String)
    location = sa.Column(sa.String)
    version = sa.Column(sa.String)
    dep_target = sa.Column(sa.String)
    status = sa.Column(sa.String)
    output_config = sa.Column(sa.Text)
    env_id = sa.Column(sa.Integer)
    
    def __init__(self):
        db_base.init()

    def save(self, app_data):
        app = App()
        app.name = app_data['name']
        app.location = app_data['location']
        app.version = app_data['version']
        app.dep_target = app_data['dep_target']
        app.status = ''
        app.output_config = ''
        app.env_id = int(app_data['env_id'])
        session = db_base.Session()
        session.add(app)
        session.commit()
        return app