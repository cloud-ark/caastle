#!/bin/bash

echo "Running tests from tests.server.dbmodule.objects.test_app"
nosetests --tests tests.server.dbmodule.objects.test_app

echo "Running tests from tests.server.dbmodule.objects.test_env"
nosetests --tests tests.server.dbmodule.objects.test_env

echo "Running functional tests"

has_server_started=`ps -eaf | grep -v grep | grep fmserver`

if [[ -z "${has_server_started}" ]]; then
    echo "CloudARK server not running. Please start the server and then run the tests."
    exit 
fi

nosetests --tests tests.server.local.test_local:TestLocal.test_app_deploy_hello_world



