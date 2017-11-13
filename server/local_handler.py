import ast
import subprocess
import time

from stevedore import extension

from common import common_functions
from common import constants
from common import docker_lib
from common import fm_logger
from dbmodule.objects import app as app_db
from server.dbmodule.objects import container as cont_db

fmlogger = fm_logger.Logging()

tagged_images_file = 'tagged_images.txt'


class LocalHandler(object):

    res_mgr = extension.ExtensionManager(
        namespace='server.server_plugins.local.resource',
        invoke_on_load=True,
    )

    coe_mgr = extension.ExtensionManager(
        namespace='server.server_plugins.local.coe',
        invoke_on_load=True,
    )

    def __init__(self):
        self.docker_handler = docker_lib.DockerLib()

    def _build_container(self, cont_info):
        df_dir = common_functions.get_df_dir(cont_info)
        cont_name = cont_info['cont_name']
        fmlogger.debug("Container name that will be used in building:%s" % cont_name)

        tag = str(int(round(time.time() * 1000)))

        err, output = self.docker_handler.build_container_image(cont_name, df_dir + "/Dockerfile",
                                                                df_context=df_dir, tag=tag)

        tagged_image = cont_name + ":" + tag

        cont_data = {}
        cont_details = {'tagged_image': tagged_image}
        cont_data['output_config'] = str(cont_details)
        cont_data['status'] = constants.CONTAINER_READY

        cont_db.Container().update(cont_name, cont_data)

        return err, output, tagged_image

    def create_container(self, cont_name, cont_info):
        df_dir = common_functions.get_df_dir(cont_info)
        cont_data = {}
        cont_data['status'] = 'building-container'

        cont_db.Container().update(cont_name, cont_data)

        err, output, cont_name = self._build_container(cont_info)
        if err:
            fmlogger.debug("Encountered error in building application container:%s. Returning." % cont_name)
            return

    def delete_container(self, tagged_name, cont_info):
        err, output = self.docker_handler.remove_container_image(tagged_name)
        if err:
            fmlogger.error(err)
            cont_db.Container().update(cont_info['cont_name'], {'status': str(err)})
        else:
            cont_db.Container().delete(cont_info['cont_name'])

    def create_cluster(self, env_id, env_info):
        coe_type = common_functions.get_coe_type(env_id)
        for name, ext in LocalHandler.coe_mgr.items():
            if name == coe_type:
                status = ext.obj.create_cluster(env_id, env_info)
                return status

    def delete_cluster(self, env_id, env_info, resource):
        coe_type = common_functions.get_coe_type(env_id)
        for name, ext in LocalHandler.coe_mgr.items():
            if name == coe_type:
                ext.obj.delete_cluster(env_id, env_info, resource)

    def deploy_application(self, app_id, app_info):
        coe_type = common_functions.get_coe_type_for_app(app_id)
        for name, ext in LocalHandler.coe_mgr.items():
            if name == coe_type:
                ext.obj.deploy_application(app_id, app_info)

    def delete_application(self, app_id, app_info):
        coe_type = common_functions.get_coe_type_for_app(app_id)
        for name, ext in LocalHandler.coe_mgr.items():
            if name == coe_type:
                ext.obj.delete_application(app_id, app_info)