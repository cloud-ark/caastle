import ast
import datetime
import os
import requests
import tarfile
import time
import subprocess
import yaml

from os.path import expanduser

import fm_logger
from server.dbmodule.objects import app as app_db
from server.dbmodule.objects import environment as env_db
from server.dbmodule.objects import resource as res_db

home_dir = expanduser("~")

APP_STORE_PATH = ("{home_dir}/.cld/data/deployments").format(home_dir=home_dir)

CONT_STORE_PATH = ("{home_dir}/.cld/data/deployments/containers").format(home_dir=home_dir)

fmlogging = fm_logger.Logging()


def untar_the_app(app_tar_file, versioned_app_path):
    fmlogging.debug("Untarring received app tar file %s" % app_tar_file)
    os.chdir(versioned_app_path)
    tar = tarfile.open(app_tar_file)
    tar.extractall(path=versioned_app_path)
    tar.close()


def get_version_stamp():
    ts = time.time()
    version_stamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d-%H-%M-%S')
    return version_stamp


def store_container_df(cont_name, cont_tar_name, content):
    cont_store_path = ("{CONT_STORE_PATH}/{cont_name}").format(CONT_STORE_PATH=CONT_STORE_PATH,
                                                               cont_name=cont_name)
    if not os.path.exists(cont_store_path):
        os.makedirs(cont_store_path)

    cont_tar_file = ("{cont_store_path}/{cont_tar_name}").format(cont_store_path=cont_store_path,
                                                                 cont_tar_name=cont_tar_name)
    df_file = open(cont_tar_file, "w")
    df_file.write(content.encode("ISO-8859-1"))
    df_file.flush()
    df_file.close()

    # expand the directory
    untar_the_app(cont_tar_file, versioned_app_path)
    return versioned_app_path, app_version

    return cont_store_path


def store_app_contents(app_name, app_tar_name, content, app_version=''):
    # create directory
    app_path = ("{APP_STORE_PATH}/{app_name}").format(APP_STORE_PATH=APP_STORE_PATH, app_name=app_name)
    if not os.path.exists(app_path):
        os.makedirs(app_path)

    if not app_version:
        app_version = get_version_stamp()

    versioned_app_path = ("{app_path}/{st}").format(app_path=app_path, st=app_version)
    if not os.path.exists(versioned_app_path):
        os.makedirs(versioned_app_path)

    # store file content
    app_tar_file = ("{versioned_app_path}/{app_tar_name}").format(versioned_app_path=versioned_app_path,
                                                                  app_tar_name=app_tar_name)
    app_file = open(app_tar_file, "w")
    app_file.write(content.encode("ISO-8859-1"))
    app_file.flush()
    app_file.close()

    # expand the directory
    untar_the_app(app_tar_file, versioned_app_path)
    return versioned_app_path, app_version


def _get_env_value(resource_list, placeholder_env_value):
    env_value = ''
    parts = placeholder_env_value.split("_")
    resource_type = parts[1]
    resource_property = parts[2]

    for resource in resource_list:
        if resource.type == resource_type.lower():
            resource_desc = resource.filtered_description
            res_desc_dict = ast.literal_eval(resource_desc)
            env_value = res_desc_dict[resource_property.rstrip()]

    return env_value


def read_app_yaml(app_info):
    app_dir = app_info['app_location']
    app_folder_name = app_info['app_folder_name']
    df_dir = app_dir + "/" + app_folder_name
    app_yaml = app_info['app_yaml']
    try:
        fp = open(df_dir + "/" + app_yaml, "r")
    except Exception as e:
        print(e)
        exit()

    try:
        app_yaml_def = yaml.load(fp.read())
    except Exception as exp:
        print("Error parsing %s" % app_yaml)
        print(exp)
        exit()
    return app_yaml_def


def resolve_environment(app_id, app_info):
    resource_list = res_db.Resource().get_resources_for_env(app_info['env_id'])

    app_yaml_def = read_app_yaml(app_info)
    env_vars = ''
    new_env_var = dict()
    if 'env' in app_yaml_def['app']:
        env_vars = app_yaml_def['app']['env']
        for key, value in env_vars.iteritems():
            if value.find("$CLOUDARK_") >= 0:
                value = _get_env_value(resource_list, value)
            new_env_var[key] = value

    return new_env_var


def is_app_ready(app_url, app_id='', timeout=300):
    ready = False
    count = 0
    num_of_oks = 10
    oks = 0
    while count < timeout and not ready:
        try:
            response = requests.get(app_url)
            if response.status_code == 200:
                oks = oks + 1
                if oks == num_of_oks:
                    ready = True
                    break
        except Exception as e:
            fmlogging.error(e)
            continue
        count = count + 1
        time.sleep(3)

    # After every 10 counts check if app still exists
    if app_id:
        if count % 10 == 0:
            app_obj = app_db.App().get(app_id)
            if not app_obj:
                count = timeout

    return ready


def save_image_tag(tag, app_info, file_name='container_id.txt'):
    tag = tag + "\n"
    save_container_id(tag, app_info, file_name)


def save_container_id(cont_id, app_info, file_name='container_id.txt'):
    app_dir = app_info['app_location']
    fp = open(app_dir + "/" + file_name, "a")
    fp.write(cont_id)
    fp.flush()
    fp.close()


def read_image_tag(app_info, file_name='container_id.txt'):
    cont_id_list = read_container_id(app_info, file_name)
    return cont_id_list


def read_container_id(app_info, file_name='container_id.txt'):
    cont_id_list = []
    try:
        app_dir = app_info['app_location']
        fp = open(app_dir + "/" + file_name, "r")
        cont_id_list = fp.readlines()
    except Exception as e:
        fmlogging.error("Error encountered in reading container_id: %s" % e)
    return cont_id_list


def get_cloud_setup():
    cloud_setup = []
    if os.path.exists(home_dir + "/.aws/credentials") and os.path.exists(home_dir + "/.aws/config"):
        cloud_setup.append("aws")
    if os.path.exists(home_dir + "/.config/gcloud"):
        cloud_setup.append("gcloud")
    return cloud_setup


def get_df_dir(cont_info):
    df_dir = cont_info['cont_store_path']
    df_dir = df_dir + "/" + cont_info['cont_df_folder_name']
    return df_dir


def get_image_uri(app_info):
    image_uri = ''
    app_yaml_def = read_app_yaml(app_info)
    image_uri = app_yaml_def['app']['image']
    return image_uri


def get_app_port(app_info):
    app_port = []
    app_yaml_def = read_app_yaml(app_info)
    if 'container_port' in app_yaml_def['app']:
        app_port.append(app_yaml_def['app']['container_port'])
    if 'host_port' in app_yaml_def['app']:
        app_port.append(app_yaml_def['app']['host_port'])
    else:
        app_port.append(80)
    return app_port


def get_app_memory(app_info):
    app_memory = ''
    app_yaml_def = read_app_yaml(app_info)
    if 'memory' in app_yaml_def['app']:
        app_memory = app_yaml_def['app']['memory']
    return app_memory


def get_coe_type(env_id):
    coe_type = ''
    env_obj = env_db.Environment().get(env_id)
    env_definition = ast.literal_eval(env_obj.env_definition)
    env_details = env_definition['environment']
    coe_type = env_details['app_deployment']['type']
    return coe_type


def get_coe_type_for_app(app_id):
    app_obj = app_db.App().get(app_id)
    coe_type = get_coe_type(app_obj.env_id)
    return coe_type


def get_app_type(app_id):
    app_obj = app_db.App().get(app_id)
    app_yaml_contents = ast.literal_eval(app_obj.app_yaml_contents)
    if 'app' in app_yaml_contents:
        return 'single-container'
    if 'apiVersion' in app_yaml_contents and 'kind' in app_yaml_contents:
        return 'multi-container'
    return coe_type


def execute_cmd(cmd):
    err= ''
    output=''
    try:
        chanl = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, shell=True).communicate()
        err = chanl[1]
        output = chanl[0]
    except Exception as e:
        fmlogging.error(e)
    return err, output
