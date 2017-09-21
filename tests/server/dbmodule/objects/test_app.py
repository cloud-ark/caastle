from random import randint
import sys
from testtools import TestCase

from server.dbmodule.objects import app
from server.dbmodule import db_base

class TestApp(TestCase):

    @classmethod
    def setUpClass(self):
        app.db_base.DBFILE_NAME="test-cld-app.sqlite"

    @classmethod
    def tearDownClass(self):
        app.db_base.delete_db_file(app.db_base.DBFILE_NAME)

    def test_app_insert(self):
        app_data = {}
        app_data['name'] = 'abc'
        app_data['location'] = 'abc'
        app_data['version'] = 'version'
        app_data['dep_target'] = 'local'
        app_data['env_id'] = 1
        new_app = app.App().insert(app_data)
        self.assertIsNotNone(new_app.id, "App not inserted properly")

    def test_app_insert_same_name(self):
        app_data = {}
        app_data['name'] = 'abc'
        app_data['location'] = 'abc'
        app_data['version'] = 'version'
        app_data['dep_target'] = 'local'
        app_data['env_id'] = 1
        new_app = app.App().insert(app_data)

        new_app1 = app.App().insert(app_data)

        self.assertIsNone(new_app1.id, "App not inserted properly")

    def test_app_delete(self):
        app_data = {}
        app_data['name'] = 'abc'
        app_data['location'] = 'abc'
        app_data['version'] = 'version'
        app_data['dep_target'] = 'local'
        app_data['env_id'] = 1
        new_app = app.App().insert(app_data)
        app.App().delete(new_app.id)
        deleted_app = app.App().get(new_app.id)
        self.assertIsNone(deleted_app)

    def test_app_update(self):
        app_data = {}
        rand_string = str(randint(0, 100))
        app_data['name'] = 'abc' + rand_string
        app_data['location'] = 'abc'
        app_data['version'] = 'version'
        app_data['dep_target'] = 'local'
        app_data['env_id'] = 1

        new_app = app.App().insert(app_data)
        self.assertEqual('version', new_app.version)

        app_data1 = {}
        app_data1['version'] = 'version1'
        app_data1['location'] = 'location'
        app.App().update(new_app.id, app_data1)
        updated_app = app.App().get(new_app.id)
        self.assertEqual('version1', app_data1['version'])

    def test_app_get_non_existing_app(self):
        app1 = app.App().get(randint(100, 200))
        self.assertIsNone(app1)