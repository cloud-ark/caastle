import os
from os.path import expanduser
import re
import yaml

home_dir = expanduser("~")

def get_app_folder_name(app_location):
    last_slash_index = app_location.rfind("/")
    app_folder_name = app_location[last_slash_index+1:]
    return app_folder_name

def check_env_name(env_name, regex_list):

    match = False

    for regex in regex_list:
        mach = re.search(regex, env_name)
        if mach:
            match = match or True
        else:
            match = match or False
    
    return match

def cloud_setup(cloud):

    setup_done = False

    if cloud == 'local':
        #TODO - Check if Docker is installed or not
        setup_done = True

    if cloud == 'gcloud':
        if os.path.exists(home_dir + "/.config/gcloud"):
            setup_done = True

    if cloud == 'aws':
        if os.path.exists(home_dir + "/.aws"):
            setup_done = True

    return setup_done

def parse_clouds(environment_def):
    cloud_list = []
    resource_list = ''
    if 'resources' in environment_def['environment']:
        resource_list = environment_def['environment']['resources']
        if 'gcloud' in resource_list:
            cloud_list.append('gcloud')
        if 'aws' in resource_list:
            cloud_list.append('aws')
        if 'local-docker' in resource_list:
            cloud_list.append('local')

    if 'app_deployment' in environment_def['environment']:
        app_deployment = environment_def['environment']['app_deployment']
        target = app_deployment['target']
        if target not in cloud_list:
            cloud_list.append(target)

    return cloud_list


def validate_app_format(app_file_name):
    valid = False
    kind_set = []
    try:
        stream = open(app_file_name, "r")
        docs = yaml.load_all(stream)
        for doc in docs:
            for k,v in doc.items():
                if k == 'kind':
                    kind_set.append(v.strip())
                if k == 'app':
                    valid = True
                    break
        if len(kind_set) == 1 and 'Pod' in kind_set:
            valid = True
    except Exception as e:
        print("Could not parse %s" % app_file_name)
        exit()
    return valid