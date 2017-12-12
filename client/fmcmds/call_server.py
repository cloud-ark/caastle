import gzip
import json
import os
import requests
import tarfile
import urllib2

resources_endpoint = "http://localhost:5002/resources"
resource_stacks_endpoint = "http://localhost:5002/resource_stacks"
environments_endpoint = "http://localhost:5002/environments"
apps_endpoint = "http://localhost:5002/apps"
containers_endpoint = "http://localhost:5002/containers"

SERVER_ERROR = "Something caused error in cloudark. Please submit bug report on cloudark github repo. "
SERVER_ERROR = SERVER_ERROR + "Attach logs from cld.log which is available in cloudark directory."


class TakeAction(object):

    def __init__(self):
        pass

    def _make_tarfile(self, output_filename, source_dir):
        with tarfile.open(output_filename, "w:gz") as tar:
            tar.add(source_dir, arcname=os.path.basename(source_dir))

    def _read_tarfile(self, tarfile_name):
        with gzip.open(tarfile_name, "rb") as f:
            contents = f.read()
            return contents

    def _delete_tarfile(self, tarfile_name, source_dir):
        cwd = os.getcwd()
        os.chdir(source_dir)
        if os.path.exists(tarfile_name):
            os.remove(tarfile_name)
        os.chdir(cwd)

    def _check_server(self):
        try:
            req = urllib2.Request(apps_endpoint)
            urllib2.urlopen(req)
        except Exception as e:
            print("CloudARK server is not running. Please run ./start-cloudark.sh.")
            exit()

    def create_container(self, source_dir, cont_info):
        self._check_server()

        req = urllib2.Request(containers_endpoint)
        req.add_header('Content-Type', 'application/octet-stream')

        cont_name = cont_info['cont_name']
        tarfile_name = cont_name + ".tar"

        self._make_tarfile(tarfile_name, source_dir)
        tarfile_content = self._read_tarfile(tarfile_name)

        cont_info['cont_tar_name'] = tarfile_name
        cont_info['content'] = tarfile_content

        cont_url = ''
        try:
            data = {'cont_info': cont_info}
            response = urllib2.urlopen(req, json.dumps(data, ensure_ascii=True, encoding='ISO-8859-1'))
            cont_url = response.headers.get('location')
            print("Request to create container %s accepted." % cont_name)
        except Exception as e:
            error = e.read()
            print(error)
        self._delete_tarfile(tarfile_name, source_dir)

    def get_container(self, container_name):
        self._check_server()
        cont_url = containers_endpoint + "/" + container_name
        req = urllib2.Request(cont_url)
        cont_data = ''
        try:
            response = urllib2.urlopen(req)
            cont_data = response.fp.read()
        except urllib2.HTTPError as e:
            if e.getcode() == 404:
                print("Container with name %s not found." % container_name)
        return cont_data

    def get_container_list(self):
        self._check_server()
        req = urllib2.Request(containers_endpoint)
        data = ''
        try:
            response = urllib2.urlopen(req)
            data = response.fp.read()
        except urllib2.HTTPError as e:
            print("Error occurred in querying endpoint %s" % containers_endpoint)
            print(e)
        return data

    def delete_container(self, cont_name):
        self._check_server()
        cont_url = containers_endpoint + "/" + cont_name
        response = requests.delete(cont_url)
        if response.status_code == 404:
            print("Container with name %s not found." % cont_name)
        if response.status_code == 202:
            print("Request to delete container with name %s accepted." % cont_name)
        if response.status_code == 303:
            print("Request to delete container with name %s accepted." % cont_name)
            print("*** Please delete the container image from GCR manually -- automation is not available for that yet.***")
        return response

    def deploy_app(self, app_path, app_info):
        self._check_server()
        source_dir = app_path
        app_name = app_info['app_name']
        tarfile_name = app_name + ".tar"

        self._make_tarfile(tarfile_name, source_dir)
        tarfile_content = self._read_tarfile(tarfile_name)

        app_info['app_name'] = app_name
        app_info['app_tar_name'] = tarfile_name
        app_info['app_content'] = tarfile_content

        data = {'app_info': app_info}

        req = urllib2.Request(apps_endpoint)
        req.add_header('Content-Type', 'application/octet-stream')

        app_url = ''
        try:
            response = urllib2.urlopen(req, json.dumps(data, ensure_ascii=True, encoding='ISO-8859-1'))
            app_url = response.headers.get('location')
            print("Request to deploy %s application accepted." % app_name)
        except Exception as e:
            error = e.read()
            print(error)
        self._delete_tarfile(tarfile_name, source_dir)

        return app_url
    
    def get_app(self, app_name):
        self._check_server()
        app_url = apps_endpoint + "/" + app_name
        req = urllib2.Request(app_url)
        app_data = ''
        try:
            response = urllib2.urlopen(req)
            app_data = response.fp.read()
        except urllib2.HTTPError as e:
            if e.getcode() == 404:
                print("App with name %s not found." % app_name)
        return app_data

    def get_app_logs(self, app_name):
        self._check_server()
        app_url = apps_endpoint + "/" + app_name + "/logs"
        req = urllib2.Request(app_url)
        logs_data = ''
        try:
            response = urllib2.urlopen(req)
            logs_data = response.fp.read()
        except urllib2.HTTPError as e:
            if e.getcode() == 404:
                print("App with name %s not found." % app_name)
        return logs_data

    def delete_app(self, app_name):
        self._check_server()
        app_url = apps_endpoint + "/" + app_name
        response = requests.delete(app_url)
        if response.status_code == 404:
            print("App with name %s not found." % app_name)
        if response.status_code == 202:
            print("Request to delete app with name %s accepted." % app_name)
        if response.status_code == 303:
            print("Request to delete app with name %s accepted." % app_name)
        return response
    
    def redeploy_app(self, app_path, app_info, app_name):
        self._check_server()
        app_id_url = apps_endpoint + "/" + app_name
        source_dir = app_path
        app_name = "app-redeploy-id-" + app_name
        tarfile_name = app_name + ".tar"

        self._make_tarfile(tarfile_name, source_dir)
        tarfile_content = self._read_tarfile(tarfile_name)

        app_info['app_tar_name'] = tarfile_name
        app_info['app_content'] = tarfile_content

        data = {'app_info': app_info}

        app_url = ''
        req = urllib2.Request(app_id_url)
        req.add_header('Content-Type', 'application/octet-stream')
        req.get_method = lambda: 'PUT'
        try:
            response = urllib2.urlopen(req, json.dumps(data, ensure_ascii=True, encoding='ISO-8859-1'))
            if response.code == 202:
                print("Request to redeploy app with name %s accepted." % app_name)
            app_url = response.headers.get('location')
        except Exception as e:
            if e.msg == 'NOT FOUND':
                print("App with name %s not found." % app_name)
            if e.msg == 'INTERNAL SERVER ERROR':
                print(SERVER_ERROR)
                return

        self._delete_tarfile(tarfile_name, source_dir)
        return app_url

    def get_app_list(self):
        self._check_server()
        req = urllib2.Request(apps_endpoint)
        data = ''
        try:
            response = urllib2.urlopen(req)
            data = response.fp.read()
        except urllib2.HTTPError as e:
            print("Error occurred in querying endpoint %s" % apps_endpoint)
            print(e)
        return data

    # Functions for environment
    def run_command(self, env_name, command_string):
        self._check_server()
        environment_command_endpoint = environments_endpoint + "/" + env_name + "/command"
        req = urllib2.Request(environment_command_endpoint)
        req.add_header('Content-Type', 'application/octet-stream')

        data = {'command_string': command_string,
                'environment_name': env_name}
        try:
            response = urllib2.urlopen(req, json.dumps(data, ensure_ascii=True, encoding='ISO-8859-1'))
            response_data = response.fp.read()
            resp_data_json = json.loads(response_data)
            result = resp_data_json['data']
            result_str = '\n'.join(result)
            return result_str
        except Exception as e:
            if e.msg == 'NOT FOUND':
                print("Environment with name %s not found." % env_name)
                exit()

    def create_environment(self, env_name, environment_def):
        self._check_server()
        req = urllib2.Request(environments_endpoint)
        req.add_header('Content-Type', 'application/octet-stream')

        data = {'environment_def': environment_def,
                'environment_name': env_name}
        try:
            response = urllib2.urlopen(req, json.dumps(data, ensure_ascii=True, encoding='ISO-8859-1'))
            print("Request to create environment %s accepted." % env_name)
        except Exception as e:
            if e.code == 503 or e.code == 500 or e.code == 412 or e.code == 400:
                error = e.read()
                print(error)
                exit()
        environment_url = response.headers.get('location')
        return environment_url
    
    def get_environment(self, env_name):
        self._check_server()
        env_url = environments_endpoint + "/" + env_name
        req = urllib2.Request(env_url)
        env_data = ''
        try:
            response = urllib2.urlopen(req)
            env_data = response.fp.read()
        except urllib2.HTTPError as e:
            if e.getcode() == 404:
                print("Environment with name %s not found." % env_name)
                exit()
        return env_data

    def delete_environment(self, env_name, force_flag=''):
        self._check_server()
        env_url = environments_endpoint + "/" + env_name
        if force_flag:
            env_url = environments_endpoint + "/" + env_name + "?force=" + force_flag
        response = requests.delete(env_url)
        if response.status_code == 404:
            print("Environment with name %s not found." % env_name)
        if response.status_code == 202:
            print("Request to delete env with name %s accepted." % env_name)
        if response.status_code == 412:
            print("Environment cannot be deleted as there are applications still running on it.")
        return response

    def get_environment_list(self):
        self._check_server()
        req = urllib2.Request(environments_endpoint)
        data = ''
        try:
            response = urllib2.urlopen(req)
            data = response.fp.read()
        except urllib2.HTTPError as e:
            print("Error occurred in querying endpoint %s" % environments_endpoint)
            print(e)
        return data

    # Functions for Individual resource
    def get_resources(self):
        self._check_server()
        req = urllib2.Request(resources_endpoint)
        data = ''
        try:
            response = urllib2.urlopen(req)
            data = response.fp.read()
        except urllib2.HTTPError as e:
            print(e)
        return data

    def get_resources_for_environment(self, env_name):
        self._check_server()
        req = urllib2.Request(resources_endpoint + "?env_name=%s" % env_name)
        data = ''
        try:
            response = urllib2.urlopen(req)
            data = response.fp.read()
        except urllib2.HTTPError as e:
            if e.getcode() == 404:
                print("Environment with name %s not found." % env_name)
        return data

    def create_resource(self, resource_obj):
        self._check_server()
        req = urllib2.Request(resources_endpoint)
        req.add_header('Content-Type', 'application/octet-stream')

        request_data = {'resource_info': resource_obj}

        response = urllib2.urlopen(req, json.dumps(request_data,
                                                   ensure_ascii=True,
                                                   encoding='ISO-8859-1'))

        resource_endpoint = response.headers.get('location')
        print("Resource URL:%s" % resource_endpoint)
        return resource_endpoint

    def get_resource(self, resource_id):
        self._check_server()
        resource_endpoint = resources_endpoint + "/" + resource_id
        req = urllib2.Request(resource_endpoint)
        resource_data = ''
        try:
            response = urllib2.urlopen(req)
            resource_data = response.fp.read()
        except urllib2.HTTPError as e:
            if e.getcode() == 404:
                print("Resource with resource-id %s not found." % resource_id)
        return resource_data

    def delete_resource(self, resource_id):
        self._check_server()
        resource_endpoint = resources_endpoint + "/" + resource_id
        response = requests.delete(resource_endpoint)
        if response.status_code == 404:
            print("Resource with resource-id %s not found." % resource_id)
        if response.status_code == 202:
            print("Request to delete resource with resource-id %s accepted." % resource_id)
        return response
