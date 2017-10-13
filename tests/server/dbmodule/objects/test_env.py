from random import randint
from testtools import TestCase

from server.dbmodule.objects import environment


class TestEnvironment(TestCase):

    def _get_env_name(self):
        return 'abc' + str(randint(0, 5000))

    def test_env_insert(self):
        env_data = {}
        env_data['name'] = self._get_env_name()
        env_data['location'] = 'abc'
        env_data['dep_target'] = 'local'
        env_data['env_definition'] = 'env_definition'
        env_data['env_version_stamp'] = 'version'
        new_env_id = environment.Environment().insert(env_data)
        self.assertIsNotNone(new_env_id, "Env not inserted properly")
        environment.Environment().delete(new_env_id)
