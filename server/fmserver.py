import ast
import datetime
import logging
import os
import sys
import tarfile
import time
import thread
from os.path import expanduser

from flask import Flask, jsonify, request
from flask_restful import reqparse, abort, Resource, Api

from common import constants

app = Flask(__name__)
api = Api(app)

parser = reqparse.RequestParser()
parser.add_argument('app_content', location='form')
parser.add_argument('app_name', location='form')

home_dir = expanduser("~")

APP_STORE_PATH = ("{home_dir}/.cld/data/deployments").format(home_dir=home_dir)
ENV_STORE_PATH = APP_STORE_PATH

if not os.path.exists(home_dir + "/.aws/credentials") or not os.path.exists(home_dir + "/.aws/config"):
    print(constants.AWS_SETUP_INCORRECT)
    exit()

try:
    from common import fm_logger
    from common import common_functions
    from dbmodule import db_handler
    from dbmodule import objects
    from dbmodule import db_main
    from dbmodule.objects import app as app_db
    from dbmodule.objects import environment as env_db
    from dbmodule.objects import resource as res_db
    import request_handler
    import environment_handler
    import app_handler
except Exception as e:
    if e.message == "You must specify a region.":
        print(constants.AWS_SETUP_INCORRECT)
        exit()

dbhandler = db_handler.DBHandler()

def start_thread(request_handler_thread):
    try:
        request_handler_thread.run()
    except Exception as e:
        fmlogging.error(e)

class ResourcesRestResource(Resource):

    def get(self):
        fmlogging.debug("Received GET request for all resources.")
        resp_data = {}
        
        env_id = request.args.get('env_id')

        if env_id:
            resp_data['data'] = dbhandler.get_resources_for_environment(env_id)
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

        env_id = request.args.get('env_id')
        response = jsonify(**resp_data)

        resource = res_db.get(resource_id)
        if resource:
            resp_data['data'] = resource
            response = jsonify(**resp_data)
            response.status_code = 200
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
            if not 'app_info' in args_dict:
                response.status_code = 400
            else:
                app_info = args_dict['app_info']

                app_name = app_info['app_name']
                env_id = app_info['env_id']
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
                    app_data['env_id'] = env_id
                    app_id = app_db.App().insert(app_data)
                except Exception as e:
                    fmlogging.debug(e)
                    message = ("App with name {app_name} already exists. Will not proceed.").format(app_name=app_name)
                    fmlogging.debug(message)
                    response.status_code = 400
                    response.status_message = message
                    return response
                env_obj = env_db.Environment().get(app_info['env_id'])
                if not env_obj:
                    response.status_code = 404
                    response.status_message = 'Environment not found.'
                    return response
                if not env_obj.status or env_obj.status != 'available':
                    response.status_code = 412
                    response.status_message = 'Environment not ready.'
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

                app_data['location'] = app_location
                app_data['version'] = app_version
                app_data['dep_target'] = cloud
                app_db.App().update(app_id, app_data)

                request_handler_thread = app_handler.AppHandler(app_id, app_info, action='deploy')
                thread.start_new_thread(start_thread, (request_handler_thread, ))
                response.headers['location'] = ('/apps/{app_id}').format(app_id=app_id)
        except Exception as e:
            fmlogging.error(e)
            # Send back Internal Server Error
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
    def get(self, app_id):
        resp_data = {}
        response = jsonify(**resp_data)
        app = app_db.App().get(app_id)
        if app:
            resp_data['data'] = app_db.App.to_json(app)
            response = jsonify(**resp_data)
            response.status_code = 200
        else:
            response.status_code = 404

        return response

    def put(self, app_id):
        fmlogging.debug("Received PUT request to redeploy app")

        args = request.get_json(force=True)

        response = jsonify()
        response.status_code = 202

        args_dict = dict(args)
        app_obj = db_handler.DBHandler().get_app(app_id)
        try:
            if not 'app_info' in args_dict:
                response.status_code = 400
            else:
                if app_obj:
                    app_info = args_dict['app_info']
                    app_name = app_obj[db_handler.APP_NAME]
                    app_tar_name = app_info['app_tar_name']
                    content = app_info['app_content']
                    app_info['app_name'] = app_name

                    cloud = app_obj[db_handler.APP_DEP_TARGET]
                    app_info['target'] = cloud
                    app_info['env_id'] = app_obj[db_handler.APP_ENV_ID]

                    app_version = app_obj[db_handler.APP_VERSION]
                    app_location, _ = common_functions.store_app_contents(app_name,
                                                                                    app_tar_name,
                                                                                    content,
                                                                                    app_version=app_version)
                    app_info['app_location'] = app_location
                    app_info['app_version'] = app_version
                    request_handler_thread = app_handler.AppHandler(app_id, app_info, action='redeploy')
                    thread.start_new_thread(start_thread, (request_handler_thread, ))
                    response.headers['location'] = ('/apps/{app_id}').format(app_id=app_id)
                else:
                    response.status_code = 404
        except Exception as e:
            fmlogging.error(e)
            # Send back Internal Server Error
            response.status_code = 500

        return response

    def delete(self, app_id):
        fmlogging.debug("Received DELETE request for app %s" % app_id)
        resp_data = {}

        response = jsonify(**resp_data)
        app_info = {}

        app_obj = db_handler.DBHandler().get_app(app_id)
        if app_obj:
            app_info['target'] = app_obj[db_handler.APP_DEP_TARGET]
            app_info['app_name'] = app_obj[db_handler.APP_NAME]
            app_info['app_location'] = app_obj[db_handler.APP_LOCATION]
            app_info['app_version'] = app_obj[db_handler.APP_VERSION]
            app_info['env_id'] = app_obj[db_handler.APP_ENV_ID]

            request_handler_thread = app_handler.AppHandler(app_id, app_info, action='delete')
            thread.start_new_thread(start_thread, (request_handler_thread, ))
            response.status_code = 202
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

        try:
            if not 'environment_def' in args_dict:
                response.status_code = 400
            else:
                environment_def = args_dict['environment_def']
                environment_name = args_dict['environment_name']
                env_version_stamp = common_functions.get_version_stamp()
                env_location = (ENV_STORE_PATH + "/environments/{env_name}-{env_version_stamp}").format(env_name=environment_name,
                                                                                                        env_version_stamp=env_version_stamp)
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

                response.headers['location'] = ('/environments/{env_id}').format(env_id=env_id)
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

class EnvironmentRestResource(Resource):

    def get(self, env_id):
        resp_data = {}
        response = jsonify(**resp_data)
        env = env_db.Environment().get(env_id)
        if env:
            resp_data['data'] = env_db.Environment.to_json(env)
            response = jsonify(**resp_data)
            response.status_code = 200
        else:
            response.status_code = 404
        return response

    def delete(self, env_id):
        fmlogging.debug("Received DELETE request for environment %s" % env_id)
        resp_data = {}

        response = jsonify(**resp_data)
        environment_info = {}

        env = env_db.Environment().get(env_id)
        if env:
            if not request.args.get("force"):
                app_list = db_handler.DBHandler().get_apps_on_environment(env_id)
                if app_list and len(app_list) > 0:
                    response.status_code = 412
                    response.status_message = 'Environment cannot be deleted as there are applications still running on it.'
                    return response
            environment_name = env.name
            environment_def = env.env_definition
            environment_info['name'] = environment_name
            environment_info['location'] = env.location
            request_handler_thread = environment_handler.EnvironmentHandler(env_id, environment_def, environment_info, action='delete')
            thread.start_new_thread(start_thread, (request_handler_thread, ))

            response.headers['location'] = ('/environments/{env_id}').format(env_id=env_id)
            response.status_code = 202
        else:
            response.status_code = 404
        return response

api.add_resource(AppsRestResource, '/apps')
api.add_resource(AppRestResource, '/apps/<app_id>')

api.add_resource(EnvironmentsRestResource, '/environments')
api.add_resource(EnvironmentRestResource, '/environments/<env_id>')

api.add_resource(ResourcesRestResource, '/resources')
api.add_resource(ResourceRestResource, '/resources/<resource_id>')

if __name__ == '__main__':
    try:
        if not os.path.exists(APP_STORE_PATH):
            os.makedirs(APP_STORE_PATH)
        fmlogging = fm_logger.Logging()
        fmlogging.info("Starting CloudARK server")

        from gevent.wsgi import WSGIServer
        http_server = WSGIServer(('', 5002), app)
        http_server.serve_forever()
    except Exception as e:
        fmlogging.error(e)

    #app.run(debug=True, threaded=True, host='0.0.0.0', port=5002)
