import ast
import json
import os
import subprocess
import requests
from random import randint
import time
import yaml


MAX_WAIT_COUNT = 180
SAMPLE_REPO = "https://github.com/cloud-ark/cloudark-samples.git"
SAMPLE_REPO_NAME = "cloudark-samples"

def clone_repo():
    fpath = ("/tmp/{sample_repo_name}").format(sample_repo_name=SAMPLE_REPO_NAME)
    if not os.path.exists(fpath):
        cmd = ("git clone {sample_repo} /tmp/{sample_repo_name}").format(sample_repo=SAMPLE_REPO,
                                                                         sample_repo_name=SAMPLE_REPO_NAME)
        os.system(cmd)

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

def create(create_cmd, show_cmd, status_to_check):
    available = False
    json_output = {}
    _, _ = execute_cmd(create_cmd)
    count = 0
    while not available and count < MAX_WAIT_COUNT:
        show_err, show_op = execute_cmd(show_cmd)
        json_output = json.loads(show_op)
        status = json_output['data']['status']
        if status == status_to_check:
            available = True
            break
        else:
            time.sleep(1)
            count = count + 1

    return json_output

def create_app_yaml(image):
    # set_trace() -- use for debugging when running nose tests
    try:
        fp = open("app.yaml", "r")
    except Exception as e:
        print(e)
        exit()

    try:
        app_yaml_def = yaml.load(fp.read())
    except Exception as exp:
        print("Error parsing app.yaml")
        print(exp)
        exit()
    
    app_yaml_def['app']['image'] = ''
    app_yaml_def['app']['image'] = image

    try:
        fp = open("app.yaml", "w")
    except Exception as e:
        print(e)
        exit()

    try:
        fp.write(yaml.dump(app_yaml_def))
        fp.flush()
        fp.close()
    except Exception as exp:
        print("Error writing app.yaml")
        print(exp)
        exit()
