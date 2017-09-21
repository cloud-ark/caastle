from testtools import TestCase
from server.dbmodule.objects import environment
from server.dbmodule import db_base

class TestEnvironment(TestCase):

    @classmethod
    def setUpClass(self):
        environment.db_base.DBFILE_NAME="test-cld-env.sqlite"

    @classmethod
    def tearDownClass(self):
        environment.db_base.delete_db_file(environment.db_base.DBFILE_NAME)

    def test_env_insert(self):
        env_data = {}
        env_data['name'] = 'abc'
        env_data['location'] = 'abc'
        env_data['dep_target'] = 'local'
        env_data['env_definition'] = 'env_definition'
        new_env = environment.Environment().insert(env_data)
        self.assertIsNotNone(new_env.id, "Env not inserted properly")