import ast
import os
import datetime
import logging
import sys
import tarfile
import time
import thread

from os.path import expanduser

import fm_logger
from dbmodule import db_handler

home_dir = expanduser("~")

APP_STORE_PATH = ("{home_dir}/.cld/data/deployments").format(home_dir=home_dir)

fmlogging = fm_logger.Logging()

dbhandler = db_handler.DBHandler()

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

def store_app_contents(app_name, app_tar_name, content):
    # create directory
    app_path = ("{APP_STORE_PATH}/{app_name}").format(APP_STORE_PATH=APP_STORE_PATH, app_name=app_name)
    if not os.path.exists(app_path):
        os.makedirs(app_path)

    app_version = get_version_stamp()

    versioned_app_path = ("{app_path}/{st}").format(app_path=app_path, st=app_version)
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
        if resource[db_handler.RESOURCE_TYPE] == resource_type.lower():
            resource_desc = resource[db_handler.RESOURCE_FILTERED_DESCRIPTION]
            res_desc_dict = ast.literal_eval(resource_desc)
            env_value = res_desc_dict[resource_property.rstrip()]

    return env_value

def resolve_environment(app_id, app_info):
    resource_list = dbhandler.get_resources_for_environment(app_info['env_id'])
    app_dir = app_info['app_location']
    app_folder_name = app_info['app_folder_name']
    df_dir = app_dir + "/" + app_folder_name
    os.rename(df_dir + "/Dockerfile", df_dir + "/Dockerfile.orig")
    fp = open(df_dir + "/Dockerfile", "w")
    fp1 = open(df_dir + "/Dockerfile.orig", "r")
    lines = fp1.readlines()

    for line in lines:
        line_to_write = line
        if line.find("$CLOUDARK_") >= 0:
            new_line_parts = []
            parts = line.split(" ")
            for part in parts:
                if part.find("$CLOUDARK_") >= 0:
                    translated_env_value = _get_env_value(resource_list, part)
                    new_line_parts.append(translated_env_value)
                else:
                    new_line_parts.append(part)
            line_to_write = " ".join(new_line_parts)
        fp.write(line_to_write)
        fp.write("\n")
    fp.close()
    fp1.close()

def marshall_app(app):
    output_app = {}
    app_attr_table = [None] * 8
    app_attr_table[0] = db_handler.APP_ID_COL
    app_attr_table[1] = db_handler.APP_NAME_COL
    app_attr_table[2] = db_handler.APP_LOCATION_COL
    app_attr_table[3] = db_handler.APP_VERSION_COL
    app_attr_table[4] = db_handler.APP_DEP_TARGET_COL
    app_attr_table[5] = db_handler.APP_STATUS_COL
    app_attr_table[6] = db_handler.APP_OUTPUT_CONFIG_COL
    app_attr_table[7] = db_handler.APP_ENV_ID_COL

    for idx, val in enumerate(app):
        output_app[app_attr_table[idx]] = app[idx]
    return output_app

def marshall_app_list(app_list):
    output_app_list = []
    for app in app_list:
        output_app = marshall_app(app)
        output_app_list.append(output_app)
    return output_app_list