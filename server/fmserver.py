import ast
import os
from os.path import expanduser
import thread
from datetime import datetime

from flask import Flask, jsonify, request
from flask_restful import reqparse, Resource, Api

from common import constants

app = Flask(__name__)
api = Api(app)

parser = reqparse.RequestParser()
parser.add_argument('app_content', location='form')
parser.add_argument('app_name', location='form')

home_dir = expanduser("~")

APP_STORE_PATH = ("{home_dir}/.cld/data/deployments").format(home_dir=home_dir)
ENV_STORE_PATH = APP_STORE_PATH

CLOUDARK_STATUS_FILE = "cloudark.status"

import app_handler
import container_handler
from common import common_functions
from common import exceptions
from common import fm_logger
from common import validator
from dbmodule import db_main
from dbmodule.objects import app as app_db
from dbmodule.objects import container as cont_db
from dbmodule.objects import environment as env_db
from dbmodule.objects import resource as res_db
import environment_handler


def start_thread(request_handler_thread):
    try:
        request_handler_thread.run()
    except Exception as e:
        fmlogging.error(e)


class ResourcesRestResource(Resource):

    def get(self):
        fmlogging.debug("Received GET request for all resources.")
        resp_data = {}

        env_name = request.args.get('env_name')
        all_resources = ''
        if env_name:
            env_obj = env_db.Environment().get_by_name(env_name)
            if env_obj:
                all_resources = res_db.Resource().get_resources_for_env(env_obj.id)
                resp_data['data'] = [res_db.Resource.to_json(res) for res in all_resources]
                response = jsonify(**resp_data)
                response.status_code = 200
                return response
            else:
                message = ("Environment with name {env_name} does not exist").format(env_name=env_name)
                fmlogging.debug(message)
                resp_data = {'error': message}
                response = jsonify(**resp_data)
                response.status_code = 404
                return response
        else:
            all_resources = res_db.Resource().get_all()
            resp_data['data'] = [res_db.Resource.to_json(res) for res in all_resources]
            response = jsonify(**resp_data)
            response.status_code = 200
            return response


class ResourceRestResource(Resource):

    def get(self, resource_id):
        fmlogging.debug("Received GET request for resource %s" % resource_id)
        resp_data = {}

        response = jsonify(**resp_data)

        resource = res_db.Resource().get(resource_id)
        if resource:
            resp_data['data'] = res_db.Resource.to_json(resource)
            response = jsonify(**resp_data)
            response.status_code = 200
        else:
            response.status_code = 404

        return response


class ContainersRestResource(Resource):

    def get(self):
        fmlogging.debug("Received GET request for all containers.")
        resp_data = {}

        all_containers = cont_db.Container().get_all()
        resp_data['data'] = [cont_db.Container.to_json(res) for res in all_containers]

        response = jsonify(**resp_data)
        response.status_code = 200
        return response

    def post(self):
        fmlogging.debug("Received POST request to create container")
        args = request.get_json(force=True)

        response = jsonify()
        response.status_code = 201

        args_dict = dict(args)

        try:
            if 'cont_info' not in args_dict:
                response.status_code = 400
            else:
                cont_info = args_dict['cont_info']
                content = cont_info['content']
                cont_name = cont_info['cont_name']
                cont_tar_name = cont_info['cont_tar_name']
                cont_store_path, cont_version = common_functions.store_app_contents(cont_name, cont_tar_name, content)
                cont_info['cont_store_path'] = cont_store_path
                cont_db.Container().insert(cont_info)
                request_handler_thread = container_handler.ContainerHandler(cont_name, cont_info, action='create')
                thread.start_new_thread(start_thread, (request_handler_thread, ))
                response.headers['location'] = ('/containers/{cont_name}').format(cont_name=cont_name)
        except Exception as e:
            fmlogging.error(e)
            resp_data = {'error': str(e)}
            response = jsonify(**resp_data)
            response.status_code = 500

        return response


class ContainerRestResource(Resource):
    def get(self, cont_name):
        resp_data = {}
        response = jsonify(**resp_data)
        cont = cont_db.Container().get(cont_name)
        if cont:
            resp_data['data'] = cont_db.Container.to_json(cont)
            response = jsonify(**resp_data)
            response.status_code = 200
        else:
            response.status_code = 404

        return response

    def delete(self, cont_name):
        fmlogging.debug("Received DELETE request for container %s" % cont_name)
        resp_data = {}

        response = jsonify(**resp_data)
        cont_info = {}

        cont_obj = cont_db.Container().get(cont_name)
        if cont_obj:
            output_config = ast.literal_eval(cont_obj.output_config)
            tagged_image = output_config['tagged_image']
            cont_info['dep_target'] = cont_obj.dep_target
            cont_info['cont_name'] = cont_name
            cont_info['cont_store_path'] = cont_obj.cont_store_path

            request_handler_thread = container_handler.ContainerHandler(tagged_image, cont_info, action='delete')
            thread.start_new_thread(start_thread, (request_handler_thread, ))
            response.status_code = 202
            # TODO(devdatta) Let the user know that the image for GCR needs to be deleted manually.
            if cont_obj.dep_target == 'gcr':
                response.status_code = 303
        else:
            response.status_code = 404
        return response


class AppsRestResource(Resource):

    def post(self):
        fmlogging.debug("Received POST request to deploy app")
        args = request.get_json(force=True)

        response = jsonify()
        response.status_code = 201

        args_dict = dict(args)

        try:
            if 'app_info' not in args_dict:
                response.status_code = 400
            else:
                app_info = args_dict['app_info']
                app_name = app_info['app_name']
                env_name = app_info['env_name']
                env_obj = env_db.Environment().get_by_name(env_name)
                if not env_obj:
                    message = ("Environment with name {env_name} does not exist").format(env_name=env_name)
                    fmlogging.debug(message)
                    resp_data = {'error': message}
                    response = jsonify(**resp_data)
                    response.status_code = 400
                    return response

                app_id = ''
                app_location = ''
                app_version = ''
                cloud = ''
                app_data = {}
                try:
                    app_data['name'] = app_name
                    app_data['location'] = app_location
                    app_data['version'] = app_version
                    app_data['dep_target'] = cloud
                    app_data['env_id'] = env_obj.id
                    app_data['env_name'] = env_obj.name
                    app_id = app_db.App().insert(app_data)
                except Exception as e:
                    fmlogging.debug(e)
                    raise e
                if not app_id:
                    message = ("App with name {app_name} already exists. Choose different name.").format(app_name=app_name)
                    fmlogging.debug(message)
                    resp_data = {'error': message}
                    response = jsonify(**resp_data)
                    response.status_code = 400
                    return response
                if not env_obj.status or env_obj.status != 'available':
                    message = 'Environment not ready.'
                    fmlogging.debug(message)
                    resp_data = {'error': message}
                    response = jsonify(**resp_data)
                    response.status_code = 412
                    return response
                app_tar_name = app_info['app_tar_name']
                content = app_info['app_content']
                if 'target' in app_info:
                    cloud = app_info['target']
                else:
                    env_dict = ast.literal_eval(env_obj.env_definition)
                    cloud = env_dict['environment']['app_deployment']['target']
                    app_info['target'] = cloud

                app_location, app_version = common_functions.store_app_contents(app_name, app_tar_name, content)
                app_info['app_location'] = app_location
                app_info['app_version'] = app_version
                app_info['env_id'] = env_obj.id

                app_data['location'] = app_location
                app_data['version'] = app_version
                app_data['dep_target'] = cloud
                app_data['app_yaml_contents'] = str(common_functions.read_app_yaml(app_info))
                app_db.App().update(app_id, app_data)

                try:
                    validator.validate_app_deployment(app_info, app_data, env_obj)
                except exceptions.AppDeploymentValidationFailure as e:
                    fmlogging.error(e)
                    message = e.get_message()
                    resp_data = {'error': message}
                    response = jsonify(**resp_data)
                    response.status_code = 400
                    return response

                request_handler_thread = app_handler.AppHandler(app_id, app_info, action='deploy')
                thread.start_new_thread(start_thread, (request_handler_thread, ))
                response.headers['location'] = ('/apps/{app_name}').format(app_name=app_name)
        except Exception as e:
            fmlogging.error(e)
            resp_data = {'error': str(e)}
            response = jsonify(**resp_data)
            response.status_code = 500

        return response
    
    def get(self):
        fmlogging.debug("Received GET request for all apps")
        resp_data = {}
        all_apps = app_db.App().get_all()
        resp_data['data'] = [app_db.App.to_json(app) for app in all_apps]
        response = jsonify(**resp_data)
        response.status_code = 200
        return response


class AppRestResource(Resource):
    def get(self, app_name):
        resp_data = {}
        response = jsonify(**resp_data)
        app = app_db.App().get_by_name(app_name)
        if app:
            resp_data['data'] = app_db.App.to_json(app)
            response = jsonify(**resp_data)
            response.status_code = 200
        else:
            response.status_code = 404

        return response

    def put(self, app_name):
        fmlogging.debug("Received PUT request to redeploy app")

        args = request.get_json(force=True)

        response = jsonify()
        response.status_code = 202

        args_dict = dict(args)
        app_obj = app_db.App().get_by_name(app_name)
        try:
            if 'app_info' not in args_dict:
                response.status_code = 400
            else:
                if app_obj:
                    app_info = args_dict['app_info']
                    app_name = app_obj.name
                    app_tar_name = app_info['app_tar_name']
                    content = app_info['app_content']
                    app_info['app_name'] = app_name

                    cloud = app_obj.dep_target
                    app_info['target'] = cloud
                    app_info['env_id'] = app_obj.env_id

                    app_version = app_obj.version
                    app_location, _ = common_functions.store_app_contents(app_name,
                                                                          app_tar_name,
                                                                          content,
                                                                          app_version=app_version)
                    app_info['app_location'] = app_location
                    app_info['app_version'] = app_version
                    request_handler_thread = app_handler.AppHandler(app_obj.id, app_info, action='redeploy')
                    thread.start_new_thread(start_thread, (request_handler_thread, ))
                    response.headers['location'] = ('/apps/{app_name}').format(app_name=app_name)
                else:
                    response.status_code = 404
        except Exception as e:
            fmlogging.error(e)
            response.status_code = 500

        return response

    def delete(self, app_name):
        fmlogging.debug("Received DELETE request for app %s" % app_name)
        resp_data = {}

        response = jsonify(**resp_data)
        app_info = {}

        app_obj = app_db.App().get_by_name(app_name)
        if app_obj:
            app_info['target'] = app_obj.dep_target
            app_info['app_name'] = app_obj.name
            app_info['app_location'] = app_obj.location
            app_info['app_version'] = app_obj.version
            app_info['env_id'] = app_obj.env_id

            request_handler_thread = app_handler.AppHandler(app_obj.id, app_info, action='delete')
            thread.start_new_thread(start_thread, (request_handler_thread, ))
            response.status_code = 202
            # TODO(devdatta) Let the user know that the image for GCR needs to be deleted manually.
            if app_obj.dep_target == 'gcloud':
                response.status_code = 303
        else:
            response.status_code = 404
        return response


class AppLogsRestResource(Resource):
    def get(self, app_name):
        resp_data = {}
        response = jsonify(**resp_data)
        app_obj = app_db.App().get_by_name(app_name)
        if app_obj:
            app_info = {}
            app_info['target'] = app_obj.dep_target
            app_info['app_name'] = app_obj.name
            app_info['app_location'] = app_obj.location
            app_info['app_version'] = app_obj.version
            app_output_config = ast.literal_eval(app_obj.output_config)
            app_info['app_folder_name'] = app_output_config['app_folder_name']
            app_info['env_id'] = app_obj.env_id

            request_handler = app_handler.AppHandler(app_obj.id, app_info)
            logs_data = request_handler.get_logs()

            resp_data['data'] = logs_data
            response = jsonify(**resp_data)
            response.status_code = 200
        else:
            response.status_code = 404

        return response


class EnvironmentsRestResource(Resource):

    def post(self):
        fmlogging.debug("Received POST request to create environment")
        args = request.get_json(force=True)

        response = jsonify()
        response.status_code = 201

        args_dict = dict(args)

        cloud_setup_done = common_functions.get_cloud_setup()
        if len(cloud_setup_done) == 0:
            resp_data = {}
            err_msg = 'No cloud setup found.'
            err_msg = err_msg + ' Run "cld setup aws" or "cld setup gcloud". Then restart cloudark server using the start-cloudark.sh script.'
            resp_data['error'] = err_msg
            response = jsonify(**resp_data)
            response.status_code = 412
            return response

        try:
            if 'environment_def' not in args_dict:
                response.status_code = 400
            else:
                environment_def = args_dict['environment_def']
                environment_name = args_dict['environment_name']
                env_version_stamp = common_functions.get_version_stamp()
                env_location = (ENV_STORE_PATH + "/environments/{env_name}-{env_version_stamp}").format(env_name=environment_name,
                                                                                                        env_version_stamp=env_version_stamp)

                mkdir_env_location = ("mkdir {env_dir}").format(env_dir=env_location)
                os.system(mkdir_env_location)

                env_data = {}
                env_data['name'] = environment_name
                env_data['location'] = env_location
                env_data['env_version_stamp'] = env_version_stamp
                env_data['env_definition'] = environment_def
                env_id = env_db.Environment().insert(env_data)
                environment_info = {}
                environment_info['name'] = environment_name

                environment_info['location'] = env_location
                request_handler_thread = environment_handler.EnvironmentHandler(env_id, environment_def, environment_info, action='create')
                thread.start_new_thread(start_thread, (request_handler_thread, ))

                response.headers['location'] = ('/environments/{env_name}').format(env_name=environment_name)
        except OSError as oe:
            fmlogging.error(oe)
            response.status_code = 503

        return response

    def get(self):
        fmlogging.debug("Received GET request for all environments")
        resp_data = {}

        all_envs = env_db.Environment().get_all()
        resp_data['data'] = [env_db.Environment.to_json(env) for env in all_envs]

        response = jsonify(**resp_data)
        response.status_code = 200
        return response

class EnvironmentRunCommandRestResource(Resource):

    def post(self, env_name):
        fmlogging.debug("Received POST request to run command on environment")
        args = request.get_json(force=True)

        response = jsonify()
        response.status_code = 201

        args_dict = dict(args)

        resp_data = {}

        try:
            if 'command_string' not in args_dict:
                response.status_code = 400
            else:
                command_string = args_dict['command_string']
                environment_name = args_dict['environment_name']

                env_obj = env_db.Environment().get_by_name(env_name)

                if not env_obj or env_obj.status == 'create-failed':
                    response.status_code = 404
                    return response

                environment_def = env_obj.env_definition
                environment_info = {'name': env_name}

                commond_output = []

                envhandler = environment_handler.EnvironmentHandler(env_obj.id,
                                                                        environment_def,
                                                                        environment_info,
                                                                        action='run_command')
                command_output = envhandler.run_command(env_name, command_string)
                resp_data['data'] = command_output
                response = jsonify(**resp_data)

                fmlogging.debug("Executing %s command on %s environment." % (command_string, environment_name))

        except OSError as oe:
            fmlogging.error(oe)
            response.status_code = 503

        return response

class EnvironmentRestResource(Resource):

    def get(self, env_name):
        resp_data = {}
        response = jsonify(**resp_data)
        env = env_db.Environment().get_by_name(env_name)
        if env:
            app_json = ''
            app_list = app_db.App().get_apps_for_env(env.id)
            if app_list:
                app_json = [app_db.App.to_json_restricted(app) for app in app_list]

            resp_data['data'] = env_db.Environment.to_json(env, app_json)
            response = jsonify(**resp_data)
            response.status_code = 200
        else:
            response.status_code = 404
        return response

    def delete(self, env_name):
        fmlogging.debug("Received DELETE request for environment %s" % env_name)
        resp_data = {}

        response = jsonify(**resp_data)
        environment_info = {}

        env = env_db.Environment().get_by_name(env_name)
        if env:
            if not request.args.get("force"):
                app_list = app_db.App().get_apps_for_env(env.id)
                if app_list and len(app_list) > 0:
                    response.status_code = 412
                    response.status_message = 'Environment cannot be deleted as there are applications still running on it.'
                    return response
            environment_name = env.name
            environment_def = env.env_definition
            environment_info['name'] = environment_name
            environment_info['location'] = env.location
            request_handler_thread = environment_handler.EnvironmentHandler(env.id, environment_def, environment_info, action='delete')
            thread.start_new_thread(start_thread, (request_handler_thread, ))

            response.headers['location'] = ('/environments/{env_name}').format(env_name=environment_name)
            response.status_code = 202
        else:
            response.status_code = 404
        return response


api.add_resource(AppsRestResource, '/apps')
api.add_resource(AppRestResource, '/apps/<app_name>')
api.add_resource(AppLogsRestResource, '/apps/<app_name>/logs')

api.add_resource(ContainersRestResource, '/containers')
api.add_resource(ContainerRestResource, '/containers/<cont_name>')

api.add_resource(EnvironmentsRestResource, '/environments')
api.add_resource(EnvironmentRestResource, '/environments/<env_name>')
api.add_resource(EnvironmentRunCommandRestResource, '/environments/<env_name>/command')

api.add_resource(ResourcesRestResource, '/resources')
api.add_resource(ResourceRestResource, '/resources/<resource_id>')

if __name__ == '__main__':
    try:
        if os.path.exists(CLOUDARK_STATUS_FILE):
            os.remove(CLOUDARK_STATUS_FILE)

        if not os.path.exists(APP_STORE_PATH):
            os.makedirs(APP_STORE_PATH)
        fmlogging = fm_logger.Logging()
        fmlogging.info("Starting CloudARK server")

        # Setup tables
        db_main.setup_tables()

        fp = open(CLOUDARK_STATUS_FILE, "w")
        current_time = str(datetime.now())
        fp.write("CloudARK started %s" % current_time)
        fp.close()

        from gevent.wsgi import WSGIServer
        http_server = WSGIServer(('', 5002), app)
        http_server.serve_forever()

    except Exception as e:
        fmlogging.error(e)

    # app.run(debug=True, threaded=True, host='0.0.0.0', port=5002)
