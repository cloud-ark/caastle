from dbmodule import db_base
from objects import app
from objects import environment
from objects import resource
from server.common import fm_logger

fmlogger = fm_logger.Logging()

def setup_tables():
    try:
        app.App.__table__.create(bind=db_base.engine)
        environment.Environment.__table__.create(bind=db_base.engine)
        resource.Resource.__table__.create(bind=db_base.engine)
    except Exception as e:
        fmlogger.debug(e)
