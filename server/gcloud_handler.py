from os.path import expanduser

from stevedore import extension

from common import fm_logger
from dbmodule.objects import environment as env_db

home_dir = expanduser("~")

APP_AND_ENV_STORE_PATH = ("{home_dir}/.cld/data/deployments/").format(home_dir=home_dir)

fmlogger = fm_logger.Logging()


class GCloudHandler(object):

    res_mgr = extension.ExtensionManager(
        namespace='server.server_plugins.gcloud.resource',
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
