import ast
from os.path import expanduser

from stevedore import extension

from common import common_functions
from common import fm_logger
from dbmodule.objects import app as app_db
from dbmodule.objects import environment as env_db

home_dir = expanduser("~")

APP_AND_ENV_STORE_PATH = ("{home_dir}/.cld/data/deployments/").format(home_dir=home_dir)

fmlogger = fm_logger.Logging()


class GCloudHandler(object):

    res_mgr = extension.ExtensionManager(
        namespace='server.server_plugins.gcloud.resource',
        invoke_on_load=True,
    )

    coe_mgr = extension.ExtensionManager(
        namespace='server.server_plugins.gcloud.coe',
        invoke_on_load=True,
    )

    app_mgr = extension.ExtensionManager(
        namespace='server.server_plugins.gcloud.app',
        invoke_on_load=True,
    )

    def create_resources(self, env_id, resource_list):
        fmlogger.debug("GCloudHandler create_resources")
        resource_details = ''
        ret_status_list = []

        for resource_defs in resource_list:
            resource_details = resource_defs['resource']
            type = resource_details['type']
            env_db.Environment().update(env_id, {'status': 'creating_' + type})

            for name, ext in GCloudHandler.res_mgr.items():
                if name == type:
                    status = ext.obj.create(env_id, resource_details)
                    if status: ret_status_list.append(status)

        return ret_status_list

    def delete_resource(self, env_id, resource):
        fmlogger.debug("GCloudHandler delete_resource")
        type = resource.type
        env_db.Environment().update(env_id, {'status': 'deleting_' + type})
        for name, ext in GCloudHandler.res_mgr.items():
            if name == type:
                ext.obj.delete(resource)

    def create_cluster(self, env_id, env_info):
        coe_type = common_functions.get_coe_type(env_id)
        for name, ext in GCloudHandler.coe_mgr.items():
            if name == coe_type:
                status = ext.obj.create_cluster(env_id, env_info)
                return status

    def delete_cluster(self, env_id, env_info, resource):
        coe_type = common_functions.get_coe_type(env_id)
        for name, ext in GCloudHandler.coe_mgr.items():
            if name == coe_type:
                ext.obj.delete_cluster(env_id, env_info, resource)

    def create_container(self, cont_name, cont_info):
        repo_type = cont_info['dep_target']
        for name, ext in GCloudHandler.res_mgr.items():
            if name == repo_type:
                ext.obj.create(cont_name, cont_info)

    def delete_container(self, cont_name, cont_info):
        repo_type = cont_info['dep_target']
        for name, ext in GCloudHandler.res_mgr.items():
            if name == repo_type:
                ext.obj.delete(cont_name, cont_info)

    # App functions
    def deploy_application(self, app_id, app_info):
        app_type = common_functions.get_app_type(app_id)
        for name, ext in GCloudHandler.app_mgr.items():
            if name == app_type:
                ext.obj.deploy_application(app_id, app_info)

    def delete_application(self, app_id, app_info):
        app_type = common_functions.get_app_type(app_id)
        for name, ext in GCloudHandler.app_mgr.items():
            if name == app_type:
                ext.obj.delete_application(app_id, app_info)

    def get_logs(self, app_id, app_info):
        log_lines = ''
        app_type = common_functions.get_app_type(app_id)
        for name, ext in GCloudHandler.app_mgr.items():
            if name == app_type:
                log_lines = ext.obj.get_logs(app_id, app_info)
        return log_lines