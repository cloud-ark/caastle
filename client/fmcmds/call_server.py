import logging
import json 
import tarfile
import urllib2
import os
import gzip
import requests

resources_endpoint = "http://localhost:5002/resources"
resource_stacks_endpoint = "http://localhost:5002/resource_stacks"
environments_endpoint = "http://localhost:5002/environments"
apps_endpoint = "http://localhost:5002/apps"

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

    def deploy_app(self, app_path, app_info):
        source_dir = app_path
        k = source_dir.rfind("/")
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

        response = urllib2.urlopen(req, json.dumps(data, ensure_ascii=True, encoding='ISO-8859-1'))

        if response.code == '503':
            print("Received 503 from server.")
            return
        if response.code == '412':
            print("App cannot be deployed as Environment is not ready.")
            return
        app_url = response.headers.get('location')
        self._delete_tarfile(tarfile_name, source_dir)

        return app_url
    
    def get_app(self, app_id):
        app_url = apps_endpoint + "/" + app_id
        req = urllib2.Request(app_url)
        app_data = ''
        try:
            response = urllib2.urlopen(req)
            app_data = response.fp.read()
        except urllib2.HTTPError as e:
            if e.getcode() == 404:
                print("App with app-id %s not found." % app_id)
        return app_data

    def delete_app(self, app_id):
        app_url = apps_endpoint + "/" + app_id
        response = requests.delete(app_url)
        if response.status_code == 404:
            print("App with id %s not found." % app_id)
        if response.status_code == 202:
            print("Request to delete app with id %s accepted." % app_id)
        return response
    
    def redeploy_app(self, app_path, app_info, app_id):
        app_id_url = apps_endpoint + "/" + app_id
        source_dir = app_path
        k = source_dir.rfind("/")
        app_name = "app-redeploy-id-" + app_id 
        tarfile_name = app_name + ".tar"

        self._make_tarfile(tarfile_name, source_dir)
        tarfile_content = self._read_tarfile(tarfile_name)

        app_info['app_tar_name'] = tarfile_name
        app_info['app_content'] = tarfile_content

        data = {'app_info': app_info}

        req = urllib2.Request(app_id_url)
        req.add_header('Content-Type', 'application/octet-stream')
        req.get_method = lambda: 'PUT'
        response = urllib2.urlopen(req, json.dumps(data, ensure_ascii=True, encoding='ISO-8859-1'))

        if response.code == '503':
            print("Received 503 from server.")
            return
        app_url = response.headers.get('location')
        self._delete_tarfile(tarfile_name, source_dir)

        return app_url
        

    def get_app_list(self):
        req = urllib2.Request(apps_endpoint)
        data = ''
        try:
            response = urllib2.urlopen(req)
            data = response.fp.read()
        except urllib2.HTTPError as e:
            print("Error occurred in querying endpoint %s" % apps_endpoint)
        return data

    # Functions for environment
    def create_environment(self, env_name, environment_def):
        req = urllib2.Request(environments_endpoint)
        req.add_header('Content-Type', 'application/octet-stream')

        data = {'environment_def': environment_def,
                'environment_name': env_name}

        response = urllib2.urlopen(req, json.dumps(data, ensure_ascii=True, encoding='ISO-8859-1'))

        environment_url = response.headers.get('location')
        print("Environment URL:%s" % environment_url)
        return environment_url
    
    def get_environment(self, env_id):
        env_url = environments_endpoint + "/" + env_id
        req = urllib2.Request(env_url)
        env_data = ''
        try:
            response = urllib2.urlopen(req)
            env_data = response.fp.read()
        except urllib2.HTTPError as e:
            if e.getcode() == 404:
                print("Environment with env-id %s not found." % env_id)
        return env_data

    def delete_environment(self, env_id):
        env_url = environments_endpoint + "/" + env_id
        response = requests.delete(env_url)
        if response.status_code == 404:
            print("Environment with id %s not found." % env_id)
        if response.status_code == 202:
            print("Request to delete env with id %s accepted." % env_id)
        if response.status_code == 412:
            print("Environment cannot be deleted as there are applications still running on it.")
        return response

    def get_environment_list(self):
        req = urllib2.Request(environments_endpoint)
        data = ''
        try:
            response = urllib2.urlopen(req)
            data = response.fp.read()
        except urllib2.HTTPError as e:
            print("Error occurred in querying endpoint %s" % environments_endpoint)
        return data

    # Functions for resource_stacks
    def get_resource_stacks(self):
        req = urllib2.Request(resource_stacks_endpoint)
        data = ''
        try:
            response = urllib2.urlopen(req)
            data = response.fp.read()
        except urllib2.HTTPError as e:
            print("Error occurred in querying endpoint %s" % resource_stacks_endpoint)
        return data

    def create_resource_stack(self, resource_info):
        req = urllib2.Request(resource_stacks_endpoint)
        req.add_header('Content-Type', 'application/octet-stream')

        data = {'resource_info': resource_info}

        response = urllib2.urlopen(req, json.dumps(data, ensure_ascii=True, encoding='ISO-8859-1'))

        rs_stack_url = response.headers.get('location')
        print("Resource Stack URL:%s" % rs_stack_url)
        return rs_stack_url

    def get_resource_stack(self, stack_id):
        stack_url = resources_stack_endpoint + "/" + stack_id
        req = urllib2.Request(stack_url)
        stack_data = ''
        try:
            response = urllib2.urlopen(req)
            stack_data = response.fp.read()
        except urllib2.HTTPError as e:
            if e.getcode() == 404:
                print("Resource stack with stack-id %s not found." % stack_id)
        return stack_data

    def delete_resource_stack(self, stack_id):
        resource_endpoint = resource_stacks_endpoint + "/" + stack_id
        response = requests.delete(resource_endpoint)
        if response.status_code == 404:
            print("Resource Stack with stack-id %s not found." % stack_id)
        if response.status_code == 202:
            print("Request to delete resource with stack-id %s accepted." % stack_id)
        return response

    # Functions for Individual resource
    def get_resources(self):
        req = urllib2.Request(resources_endpoint)
        data = ''
        try:
            response = urllib2.urlopen(req)
            data = response.fp.read()
        except urllib2.HTTPError as e:
            print("Error occurred in querying endpoint %s" % resources_endpoint)
        return data

    def get_resources_for_environment(self, env_id):
        req = urllib2.Request(resources_endpoint + "?env_id=%s" % env_id)
        data = ''
        try:
            response = urllib2.urlopen(req)
            data = response.fp.read()
        except urllib2.HTTPError as e:
            print("Error occurred in querying endpoint %s" % resources_endpoint)
        return data

    def create_resource(self, resource_obj):
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
        resource_endpoint = resources_endpoint + "/" + resource_id
        response = requests.delete(resource_endpoint)
        if response.status_code == 404:
            print("Resource with resource-id %s not found." % resource_id)
        if response.status_code == 202:
            print("Request to delete resource with resource-id %s accepted." % resource_id)
        return response

