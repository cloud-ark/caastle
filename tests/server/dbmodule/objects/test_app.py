from random import randint
from testtools import TestCase

from server.dbmodule.objects import app


class TestApp(TestCase):

    def _get_app_name(self):
        return 'abc' + str(randint(0, 5000))

    def test_app_insert(self):
        app_data = {}
        app_data['name'] = self._get_app_name()
        app_data['location'] = 'abc'
        app_data['version'] = 'version'
        app_data['dep_target'] = 'local'
        app_data['env_id'] = 1
        new_app_id = app.App().insert(app_data)
        self.assertIsNotNone(new_app_id, "App not inserted properly")
        app.App().delete(new_app_id)

    def test_app_insert_same_name(self):
        app_data = {}
        app_data['name'] = self._get_app_name()
        app_data['location'] = 'abc'
        app_data['version'] = 'version'
        app_data['dep_target'] = 'local'
        app_data['env_id'] = 1
        new_app_id = app.App().insert(app_data)
        new_app1_id = app.App().insert(app_data)

        self.assertIsNone(new_app1_id, "App not inserted properly")
        self.assertIsNotNone(new_app_id, "App not inserted properly")
        app.App().delete(new_app_id)

    def test_app_delete(self):
        app_data = {}
        app_data['name'] = self._get_app_name()
        app_data['location'] = 'abc'
        app_data['version'] = 'version'
        app_data['dep_target'] = 'local'
        app_data['env_id'] = 1
        new_app_id = app.App().insert(app_data)
        app.App().delete(new_app_id)
        deleted_app = app.App().get(new_app_id)
        self.assertIsNone(deleted_app)

    def test_app_update(self):
        app_data = {}
        app_data['name'] = self._get_app_name()
        app_data['location'] = 'abc'
        app_data['version'] = 'version'
        app_data['dep_target'] = 'local'
        app_data['env_id'] = 1

        new_app_id = app.App().insert(app_data)

        app_data1 = {}
        app_data1['version'] = 'version1'
        app_data1['location'] = 'location'
        app.App().update(new_app_id, app_data1)
        updated_app = app.App().get(new_app_id)
        self.assertEqual('version1', updated_app.version)
        app.App().delete(updated_app.id)

    def test_app_get_non_existing_app(self):
        app1 = app.App().get(randint(100, 200))
        self.assertIsNone(app1)
