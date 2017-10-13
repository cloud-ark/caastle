#!/bin/bash

echo "Running tests from tests.server.dbmodule.objects.test_app"
nosetests --tests tests.server.dbmodule.objects.test_app

echo "Running tests from tests.server.dbmodule.objects.test_env"
nosetests --tests tests.server.dbmodule.objects.test_env

