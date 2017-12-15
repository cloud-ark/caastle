import ast
import datetime
import os
import requests
import tarfile
import time
import subprocess
import yaml

from os.path import expanduser

import common_functions
import exceptions
import fm_logger
from server.dbmodule.objects import app as app_db
from server.dbmodule.objects import environment as env_db
from server.dbmodule.objects import resource as res_db

home_dir = expanduser("~")

APP_STORE_PATH = ("{home_dir}/.cld/data/deployments").format(home_dir=home_dir)

CONT_STORE_PATH = ("{home_dir}/.cld/data/deployments/containers").format(home_dir=home_dir)

fmlogging = fm_logger.Logging()


def _validate_host_port(app_info, app_data, env_obj):
    app_yaml = common_functions.read_app_yaml(app_info)

    # Currently only validating for CloudARK's yaml format
    if 'app' not in app_yaml:
        return
    apps = app_db.App().get_apps_for_env(env_obj.id)
    for app in apps:
        if app.output_config:
            app_config = ast.literal_eval(app.output_config)
            if 'host_port' in app_config and 'host_port' in app_yaml['app']:
                if app_config['host_port'] == app_yaml['app']['host_port']:
                    raise exceptions.HostPortConflictException(app_config['host_port'])

def validate_app_deployment(app_info, app_data, env_obj):
    _validate_host_port(app_info, app_data, env_obj)
