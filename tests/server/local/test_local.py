import ast
import json
import os
import subprocess
import requests
from random import randint
import time
import yaml

from nose.tools import set_trace

from tests.server import common_functions

from testtools import TestCase


class TestLocal(TestCase):

    @classmethod
    def setUpClass(cls):
        common_functions.clone_repo()

    def test_app_deploy_hello_world(self):
        cwd = os.getcwd()
        os.chdir("/tmp/cloudark-samples/hello-world")

        rand_int = str(randint(0, 5000))
        env_name = "e" + rand_int
        env_create_cmd = ("cld env create {env_name} environment-local.yaml").format(env_name=env_name)
        env_show_cmd = ("cld env show {env_name}").format(env_name=env_name)
        common_functions.create(env_create_cmd, env_show_cmd, 'available')

        cont_name = "c" + rand_int
        cont_create_cmd = ("cld container create {cont_name} local").format(cont_name=cont_name)
        cont_show_cmd = ("cld container show {cont_name}").format(cont_name=cont_name)
        cont_output = common_functions.create(cont_create_cmd, cont_show_cmd, 'container-ready')

        output_config = ast.literal_eval(cont_output['data']['output_config'])
        image = output_config['tagged_image']
        common_functions.create_app_yaml(image)

        app_name = "a" + rand_int
        app_deploy_cmd = ("cld app deploy {app_name} {env_name} app.yaml").format(app_name=app_name, env_name=env_name)
        app_show_cmd = ("cld app show {app_name}").format(app_name=app_name)
        app_output = common_functions.create(app_deploy_cmd, app_show_cmd, 'APP_DEPLOYMENT_COMPLETE')
        
        app_status = app_output['data']['status']
        self.assertEqual("APP_DEPLOYMENT_COMPLETE", app_status, "App deployment failed")

        app_delete_cmd = ("cld app delete {app_name}").format(app_name=app_name)
        common_functions.execute_cmd(app_delete_cmd)

        time.sleep(10)
        cont_delete_cmd = ("cld container delete {cont_name}").format(cont_name=cont_name)
        common_functions.execute_cmd(cont_delete_cmd)

        env_delete_cmd = ("cld env delete {env_name}").format(env_name=env_name)
        common_functions.execute_cmd(env_delete_cmd)

        os.chdir(cwd)
