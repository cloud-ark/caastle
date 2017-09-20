from testtools import TestCase
from server.dbmodule.objects import app

class TestApp(TestCase):
    
    def setUp(self):
        super(TestApp, self).setUp()
        
    def test_app_insert(self):
        app_data = {}
        app_data['name'] = 'abc'
        app_data['location'] = 'abc'
        app_data['version'] = 'version'
        app_data['dep_target'] = 'local'
        app_data['env_id'] = 1
        new_app = app.App().save(app_data)
        self.assertIsNotNone(new_app, "App not inserted properly")

